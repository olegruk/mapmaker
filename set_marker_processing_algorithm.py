# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsField,
    QgsFields,
    QgsFeature,
    QgsMessageLog,
    QgsUnitTypes
)

import processing
import os.path
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsWkbTypes,
                       QgsFeatureSink,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterBoolean,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProcessingException,
                       QgsProcessingUtils)

#from processing.core.Processing import Processing

class SetMarkerProcessingAlgorithm(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    DISTANCE = 'DISTANCE'
    LASTPOINT ='LASTPOINT'

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, 'Track layer', types=[QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterNumber(self.DISTANCE, 'Points interval:', defaultValue=1000, optional=False, minValue=1, maxValue=100000))
        self.addParameter(QgsProcessingParameterBoolean(self.LASTPOINT, 'Mark last point:', defaultValue=True, optional=False))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Markers layer', type=QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):

        in_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        distance = self.parameterAsInt(parameters, self.DISTANCE, context)
        mark_endpoint = self.parameterAsBoolean(parameters, self.LASTPOINT, context)
        out_layer = 'Distance markers'
        decimal=2

        in_layer_crs = in_layer.crs()
        final_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        grid_Wkb = QgsWkbTypes.Point

        pt = next(in_layer.getFeatures()).geometry().interpolate(0)
        pt = pt.asPoint()
        
        try:
            pt4326 = self.ConvertCoord(pt,in_layer_crs)
            crs_string = self._define_grid_crs(pt4326)
            if crs_string is not None:
                    dest_crs = QgsCoordinateReferenceSystem(crs_string)
        except Exception as e:
            raise QgsProcessingException("Invalid coordinate: {}".format(e))
        if in_layer_crs != dest_crs:
            result = processing.run('qgis:reprojectlayer', {'INPUT': in_layer, 'TARGET_CRS': crs_string, 'OUTPUT': 'memory:'})
            mid_layer = result['OUTPUT']
        else:
            mid_layer = in_layer
        
        marker_layer = self.create_markers(mid_layer, out_layer, distance, mark_endpoint)

        result = processing.run('qgis:reprojectlayer', {'INPUT': marker_layer, 'TARGET_CRS': final_crs, 'OUTPUT': 'memory:'})
        res_layer = result['OUTPUT']

        fields = res_layer.fields()
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, grid_Wkb, final_crs)

        for f in res_layer.getFeatures():
            if feedback.isCanceled():
                break
            sink.addFeature(f, QgsFeatureSink.FastInsert)

        base_path = os.path.dirname(os.path.abspath(__file__))
        result_path = os.path.join(base_path, 'styles')
        if not os.path.exists(result_path):
            feedback.pushConsoleInfo('Styles folder\n%s\ndoes not exist. Using a random styles.'%result_path)
        else:
            style_file = os.path.join(result_path, "dist_marker.qml")
            if not os.path.exists(style_file):
                feedback.pushConsoleInfo('Styles file\n%s\ndoes not exist. Using a random styles.'%style_file)
            else:
                processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id, context)
                processed_layer.loadNamedStyle(style_file)
                processed_layer.triggerRepaint()


        return {self.OUTPUT: [dest_id]}

    def ConvertCoord(self, pt, src_crs):
        '''Format the coordinate string.'''
        # ProjectionTypeWgs84
        # Make sure the coordinate is transformed to EPSG:4326
        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        if src_crs == epsg4326:
            pt4326 = pt
        else:
            transform = QgsCoordinateTransform(src_crs, epsg4326, QgsProject.instance())
            pt4326 = transform.transform(pt.x(), pt.y())
        return pt4326
        
    def _define_grid_crs(self, pt):
        zone = int(31 + pt.x() // 6)
        if zone > 60:
            zone = 60
        if zone < 10:
            new_crs_str = "EPSG:3260" + str(zone)
        else:
            new_crs_str = "EPSG:326" + str(zone)
   
        return new_crs_str

    def create_markers(self, mid_layer, out_layer, distance, mark_endpoint):

        crs = mid_layer.crs().authid()

        virt_layer = QgsVectorLayer("Point?crs=%s" % crs,
                                    out_layer,
                                    "memory")
        provider = virt_layer.dataProvider()
        virt_layer.startEditing()

        units = mid_layer.crs().mapUnits()

        unitname = QgsUnitTypes.toString(units)
        provider.addAttributes([QgsField("id", QVariant.Int),
                                QgsField("dist_"+unitname, QVariant.Double)])

        for feature in mid_layer.getFeatures():
            track = feature.geometry()
            fid = feature.id()
            if not track:
                QgsMessageLog.logMessage("No geometry", "MapMaker")
                continue

            markers = self.marks_along_track(track, distance, mark_endpoint, fid)
            provider.addFeatures(markers)

        virt_layer.commitChanges()
        #virt_layer.reload()

        return virt_layer

    def marks_along_track(self, track, distance, mark_endpoint, fid):

        length = track.length()
        if distance <= 0:
            distance = length

        fields = QgsFields()
        fields.append(QgsField(name="id", type=QVariant.Int))
        fields.append(QgsField(name="dist", type=QVariant.Double))
        
        current_distance = 0
        feats = []

        while current_distance <= length:
            # Get a point along the line at the current distance
            point = track.interpolate(current_distance)
            # convert 3D geometry to 2D geometry as OGR seems to have problems with this
            #point = QgsGeometry.fromPointXY(point.asPoint())
            # Create a new QgsFeature and assign it the new geometry
            feature = QgsFeature(fields)
            feature['dist'] = (current_distance)
            feature['id'] = fid
            feature.setGeometry(point)
            feats.append(feature)
            # Increase the distance
            current_distance = current_distance + distance

        # set the last point at endpoint if wanted
        if mark_endpoint:
            end = track.length()
            point = track.interpolate(end)
            feature = QgsFeature(fields)
            feature['dist'] = end
            feature['id'] = fid
            feature.setGeometry(point)
            feats.append(feature)
        return feats

    def name(self):
        return 'Set km markers'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/setmarker.png')

    def displayName(self):
        return self.name()

    def group(self):
        return self.groupId()

    def groupId(self):
        return ''

    def createInstance(self):
        return SetMarkerProcessingAlgorithm()
