# -*- coding: utf-8 -*-

"""
/***************************************************************************
 NamedGridProcessing
***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import processing
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsFeatureSink,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsWkbTypes,
                       QgsRectangle,
                       QgsProcessing,
                       QgsProcessingUtils,
                       QgsProcessingException,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterDistance,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem,
                       QgsVectorLayer)
import os.path
import pyproj

class NamedGridProcessingAlgorithm(QgsProcessingAlgorithm):

    EXTENT = 'EXTENT'
    HSPACING = 'HSPACING'
    VSPACING = 'VSPACING'
    CRS = 'CRS'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterExtent(self.EXTENT, 'Grid extent'))

        self.addParameter(QgsProcessingParameterDistance(self.HSPACING,
                                                         'Horizontal grid spacing',
                                                         250.0, self.CRS, False, 0, 1000000000.0))
        self.addParameter(QgsProcessingParameterDistance(self.VSPACING,
                                                         'Vertical grid spacing',
                                                         250.0, self.CRS, False, 0, 1000000000.0))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT,
                                                            'Grid',
                                                            type=QgsProcessing.TypeVectorPolygon))

    def processAlgorithm(self, parameters, context, feedback):

        current_crs = context.project().crs()
        final_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        grid_Wkb = QgsWkbTypes.Point
        
        bbox = self.parameterAsExtent(parameters, self.EXTENT, context, current_crs)
        grid_crs_str = self._define_grid_crs(bbox, current_crs)
        grid_crs = QgsCoordinateReferenceSystem(grid_crs_str)
        
        bbox_prj = self._reproj_bbox(bbox, current_crs, grid_crs)
        
        hSpacing = self.parameterAsDouble(parameters, self.HSPACING, context)
        vSpacing = self.parameterAsDouble(parameters, self.VSPACING, context)
        if hSpacing <= 0 or vSpacing <= 0:
            raise QgsProcessingException('Invalid grid spacing: {0}/{1}'.format(hSpacing, vSpacing))
        if bbox_prj.width() < hSpacing:
            raise QgsProcessingException('Horizontal spacing is too large for the covered area')
        if bbox_prj.height() < vSpacing:
            raise QgsProcessingException('Vertical spacing is too large for the covered area')
        uri_str = "Point?crs=" + grid_crs_str + "&field=name:string(5)"
        tmp_layer = QgsVectorLayer(uri_str, "temp_layer", "memory")
        tmp_provider = tmp_layer.dataProvider()

        columns = self._pointGrid(tmp_provider, bbox_prj, hSpacing, vSpacing, feedback)

        if  columns > 52:
            raise QgsProcessingException('Grid is too large for the comfort use. %s columns.' %(columns))
            
        result = processing.run('qgis:reprojectlayer', {'INPUT': tmp_layer, 'TARGET_CRS': 'EPSG:4326', 'OUTPUT': 'memory:'})
        fields = tmp_layer.fields()
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, grid_Wkb, final_crs)
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        features = result['OUTPUT'].getFeatures()
        total = 100.0 / result['OUTPUT'].featureCount() if result['OUTPUT'].featureCount() else 0
        for current, f in enumerate(features):
            if feedback.isCanceled():
                break
            sink.addFeature(f, QgsFeatureSink.FastInsert)
            feedback.setProgress(int(current * total))

        base_path = os.path.dirname(os.path.abspath(__file__))
        result_path = os.path.join(base_path, 'styles')
        if not os.path.exists(result_path):
            feedback.pushConsoleInfo('Styles folder\n%s\ndoes not exist. Using a random styles.'%result_path)
        else:
            style_file = os.path.join(result_path, "grid.qml")
            if not os.path.exists(style_file):
                feedback.pushConsoleInfo('Styles file\n%s\ndoes not exist. Using a random styles.'%style_file)
            else:
                processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id, context)
                processed_layer.loadNamedStyle(style_file)
                processed_layer.triggerRepaint()

        return {self.OUTPUT: [columns, uri_str]}

    '''
    def postProcessAlgorithm(self, context, feedback):
        root = QgsProject.instance().layerTreeRoot()
        layer_list = root.checkedLayers()
        #raise QgsProcessingException('Layer list: %s.' %(layer_list))
        feedback.pushInfo('Layer list: %s.' %(layer_list))
        return {self.OUTPUT: []}
    '''

    def _reproj_bbox(self, bbox, in_crs, out_crs):
    
        proj_in = pyproj.Proj(init=in_crs.authid())
        proj_out = pyproj.Proj(init=out_crs.authid())
        xmin, ymin = pyproj.transform(proj_in, proj_out, bbox.xMinimum(), bbox.yMinimum())
        xmax, ymax = pyproj.transform(proj_in, proj_out, bbox.xMaximum(), bbox.yMaximum())
        bbox_reproj = QgsRectangle(xmin, ymin, xmax, ymax)
        
        return bbox_reproj
        
    def _define_grid_crs(self, bbox, crs):

        center_x = bbox.center().x()
        center_y = bbox.center().y()
        proj_current = pyproj.Proj(init=crs.authid())
        proj_wgs84 = pyproj.Proj(init="epsg:4326")
        x, y = pyproj.transform(proj_current, proj_wgs84, center_x, center_y)
        zone = int(31 + x // 6)
        if zone > 60:
            zone = 60
        if zone < 10:
            new_crs_str = "EPSG:3260" + str(zone)
        else:
            new_crs_str = "EPSG:326" + str(zone)
   
        return new_crs_str


    def _pointGrid(self, lay, bbox, hSpacing, vSpacing, feedback):
        feat = QgsFeature()

        columns = int(bbox.width() // hSpacing)
        rows = int(bbox.height() // vSpacing + 1)

        cells = rows * columns
        count_update = cells * 0.05

        count = 0
        alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

        if columns <= 52:
            if columns <= 26:
                alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
            else:
                alpha = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
                for i in range(columns // 2):
                    alphabet[i] = 'L-' + alpha[i]
                    alphabet[i+columns // 2] = 'R-' + alpha[i]
                alphabet[columns - 1] = 'R-' + alpha[columns - columns // 2 - 1]
            xmin = (bbox.xMinimum() // hSpacing + 1) * hSpacing
            ymax = (bbox.yMaximum() // vSpacing) * vSpacing
            for col in range(columns):
                for row in range(rows):
                    x = xmin + col * hSpacing
                    y = ymax - row * vSpacing
                    name = alphabet[col] + str(row+1)
                    feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
                    feat.setAttributes([name])
                    lay.addFeature(feat, QgsFeatureSink.FastInsert)

                    count += 1
                    if int(count % count_update) == 0:
                        feedback.setProgress(int(count / cells * 100))
        return columns

    def name(self):
        return 'Create named grid'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/namedgrid.png')

    def displayName(self):
        return self.name()

    def group(self):
        return self.groupId()

    def groupId(self):
        return ''

    def createInstance(self):
        return NamedGridProcessingAlgorithm()
