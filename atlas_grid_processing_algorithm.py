# -*- coding: utf-8 -*-

from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsFeatureSink,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterEnum,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       #QgsProcessingParameterNumber,
                       QgsProcessingParameterScale,
                       QgsVectorLayer)
from processing.core.Processing import Processing
import os.path, math, time


class AtlasGridProcessingAlgorithm(QgsProcessingAlgorithm):

    FORMAT = 'FORMAT'
    EXTENT = 'EXTENT'
    SCALE = 'SCALE'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):

        self.formats = ['A4 portrait',
                      'A4 landscape',
                      'A3 portrait',
                      'A3 landscape',
                      'A2 portrait',
                      'A2 landscape',
                      'A1 portrait',
                      'A1 landscape',
                      'A0 portrait',
                      'A0 landscape']

        self.addParameter(QgsProcessingParameterEnum(self.FORMAT, 'Atlas format', self.formats, defaultValue=self.formats[0]))
        self.addParameter(QgsProcessingParameterScale(self.SCALE, 'Map scale', defaultValue=25000))
        #self.addParameter(QgsProcessingParameterNumber(self.SCALE, 'Grid Scale:', defaultValue=250, optional=False, minValue=0, maxValue=10000))
        self.addParameter(QgsProcessingParameterExtent(self.EXTENT, 'Atlas extent'))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Atlas Grid', type=QgsProcessing.TypeVectorPolygon))
       
    def processAlgorithm(self, parameters, context, feedback):

        crs = context.project().crs()
        fmt = self.parameterAsEnum(parameters, self.FORMAT, context)
        #scale = self.parameterAsInt(parameters, self.SCALE, context)
        scale = int(self.parameterAsDouble(parameters, self.SCALE, context)/100)
        bbox = self.parameterAsExtent(parameters, self.EXTENT, context, crs)
        grid_Wkb = QgsWkbTypes.Polygon

        page_h, page_v = self._decode_fmt(fmt, scale)

        uri_str = "Polygon?crs=" + crs.authid() + "&field=page_h:int&field=page_v:int&field=scale:int"
        atlas_layer = QgsVectorLayer(uri_str, "atlas_layer", "memory")
        atlas_provider = atlas_layer.dataProvider()
        
        self._rectangleGrid(atlas_provider, bbox, page_h, page_v, scale, feedback)
        
        fields = atlas_layer.fields()
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, grid_Wkb, crs)
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        features = atlas_layer.getFeatures()
        total = 100.0 / atlas_layer.featureCount() if atlas_layer.featureCount() else 0
        for current, f in enumerate(features):
            if feedback.isCanceled():
                break
            sink.addFeature(f, QgsFeatureSink.FastInsert)
            feedback.setProgress(int(current * total))
        
        return {self.OUTPUT: dest_id}
     
    def _rectangleGrid(self, sink, bbox, page_h, page_v, scale, feedback):
        feat = QgsFeature()

        hSpacing = (page_h-20)*scale/10
        vSpacing = (page_v-20)*scale/10

        columns = int(math.ceil(float(bbox.width()) / hSpacing))
        rows = int(math.ceil(float(bbox.height()) / vSpacing))

        cells = rows * columns
        count_update = cells * 0.05

        id = 1
        count = 0

        for col in range(columns):
            if feedback.isCanceled():
                break

            x1 = bbox.xMinimum() + (col * hSpacing)
            x2 = x1 + hSpacing

            for row in range(rows):
                y1 = bbox.yMaximum() - (row * vSpacing)
                y2 = y1 - vSpacing

                polyline = []
                polyline.append(QgsPointXY(x1, y1))
                polyline.append(QgsPointXY(x2, y1))
                polyline.append(QgsPointXY(x2, y2))
                polyline.append(QgsPointXY(x1, y2))
                polyline.append(QgsPointXY(x1, y1))

                feat.setGeometry(QgsGeometry.fromPolygonXY([polyline]))
                feat.setAttributes([int(page_h), int(page_v), int(scale)])
                sink.addFeature(feat, QgsFeatureSink.FastInsert)

                id += 1
                count += 1
                if int(math.fmod(count, count_update)) == 0:
                    feedback.setProgress(int(count / cells * 100))

    def _decode_fmt(self, fmt, scale):
        if fmt == 0: #A4 portrait
            page_h = 210
            page_v = 297
        elif fmt == 1: #A4 landscape
            page_h = 297
            page_v = 210
        elif fmt == 2: #A3 portrait
            page_h = 297
            page_v = 420
        elif fmt == 3: #A3 landscape
            page_h = 420
            page_v = 297
        elif fmt == 4: #A2 portrait
            page_h = 420
            page_v = 594
        elif fmt == 5: #A2 landscape
            page_h = 594
            page_v = 420
        elif fmt == 6: #A1 portrait
            page_h = 594
            page_v = 841
        elif fmt == 7: #A1 landscape
            page_h = 841
            page_v = 594
        elif fmt == 8: #A0 portrait
            page_h = 841
            page_v = 1189
        elif fmt == 9: #A0 landscape
            page_h = 1189
            page_v = 841

        return page_h, page_v

    def name(self):
        return 'Atlas grid'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/grid.png')

    def displayName(self):
        return self.name()

    def group(self):
        return self.groupId()

    def groupId(self):
        return ''

    def createInstance(self):
        return AtlasGridProcessingAlgorithm()
