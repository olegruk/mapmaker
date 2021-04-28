# -*- coding: utf-8 -*-

"""
/***************************************************************************
 CreateAtlasProcessingAlgorithm
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

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QRectF
from qgis.core import (QgsField,
                       QgsFields,
                       QgsFeatureSink,
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
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterFeatureSource,
                       QgsProject,
                       QgsPrintLayout,
                       QgsLayoutItemMap,
                       QgsLayoutExporter,
                       QgsLayoutSize,
                       QgsVectorLayer,
                       QgsMapLayerType)
from processing.core.Processing import Processing
import os.path, math, time


class CreateAtlasProcessingAlgorithm(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    BRIGHT = 'BRIGHT'
    CONTR = 'CONTR'
    SATUR = 'SATUR'
    FILE = 'FILE'
    PRESET = 'PRESET'

    def initAlgorithm(self, config=None):

        f_name = self._make_file_name('A4', 250)

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, 'Atlas Grid', types=[QgsProcessing.TypeVectorPolygon]))
        self.presetlist = ['Custom (the values are defined below)',
                            'Satellite (Brightness: 30, Contrast: 0, Saturation: 0)',
                            'OSM Topo (Brightness: -110, Contrast: 40, Saturation: -40)',
                            'Slazav (Brightness: 0, Contrast: 0, Saturation: 0)']
        self.addParameter(QgsProcessingParameterEnum(self.PRESET, 'Print preset', self.presetlist, defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber(self.BRIGHT, 'Map brightness:', defaultValue=0, optional=False, minValue=-500, maxValue=10000))
        self.addParameter(QgsProcessingParameterNumber(self.CONTR, 'Map contrast:', defaultValue=0, optional=False, minValue=-500, maxValue=10000))
        self.addParameter(QgsProcessingParameterNumber(self.SATUR, 'Map saturation:', defaultValue=0, optional=False, minValue=-500, maxValue=10000))
        self.addParameter(QgsProcessingParameterFileDestination(self.FILE, 'Atlas output file', '*.pdf', defaultValue=f_name))

    def processAlgorithm(self, parameters, context, feedback):

        preset = self.parameterAsEnum(parameters, self.PRESET, context)
        pdf_path = self.parameterAsFile(parameters, self.FILE, context)

        #[brightness, contrast, saturation]
        presets = [[0,0,0],[30,0,0],[-110, 40, -40],[0,0,0]]
        if preset != 0:
            bright = presets[preset][0]
            contr = presets[preset][1]
            satur = presets[preset][2]
        else:
            bright = self.parameterAsInt(parameters, self.BRIGHT, context)
            contr = self.parameterAsInt(parameters, self.CONTR, context)
            satur = self.parameterAsInt(parameters, self.SATUR, context)

        atlas_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        atlas_page = next(atlas_layer.getFeatures())

        page_h = atlas_page.attribute('page_h')
        page_v = atlas_page.attribute('page_v')
        atlas_h = page_h - 20
        atlas_v = page_v - 20
        scale = atlas_page.attribute('scale')

        root = QgsProject.instance().layerTreeRoot()
        layer_list = root.checkedLayers()
        idx,rasters = self._last_raster(layer_list)
        if idx >= 0:
            curr_bright = layer_list[idx].brightnessFilter().brightness()
            curr_contr = layer_list[idx].brightnessFilter().contrast()
            curr_satur = layer_list[idx].hueSaturationFilter().saturation()
            layer_list[idx].brightnessFilter().setBrightness(bright)
            layer_list[idx].brightnessFilter().setContrast(contr)
            layer_list[idx].hueSaturationFilter().setSaturation(satur)

        QgsProject.instance().addMapLayers(layer_list)

        self.layout = QgsPrintLayout(QgsProject.instance())
        self.layout.initializeDefaults()
        page = self.layout.pageCollection().pages()[0]
        page.setPageSize(QgsLayoutSize(page_h, page_v))

        self.atlas_map = QgsLayoutItemMap(self.layout)
        self.atlas_map.attemptSetSceneRect(QRectF(10,10, atlas_h, atlas_v))
        self.atlas_map.setFrameEnabled(True)
        self.atlas_map.setScale(scale * 100)
        self.atlas_map.setLayers(layer_list)
        self.layout.addLayoutItem(self.atlas_map)

        bbox = atlas_page.geometry().boundingBox()
        self.atlas_map.setExtent(bbox)
        self.atlas_map.setAtlasDriven(True)
        self.atlas_map.setAtlasScalingMode(QgsLayoutItemMap.Fixed)

        self.atlas = self.layout.atlas()
        self.atlas.setCoverageLayer(atlas_layer)
        self.atlas.setEnabled(True)

        exporter = QgsLayoutExporter(self.layout)

        if os.path.isfile(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError:
                raise QgsProcessingException('Unable to overwrite %s. File locked by another application.' %(pdf_path))
        exporter.exportToPdf(self.layout.atlas(), pdf_path, QgsLayoutExporter.PdfExportSettings())

        if idx >= 0:
            layer_list[idx].brightnessFilter().setBrightness(curr_bright)
            layer_list[idx].brightnessFilter().setContrast(curr_contr)
            layer_list[idx].hueSaturationFilter().setSaturation(curr_satur)

        return {'OUTPUT': [layer_list, page_h, page_v, atlas_h, atlas_v,rasters]}

    def _last_raster (self, checked_list):
        rasters = []
        for lay in checked_list:
            #if lay.dataProvider().name() == 'wms':
            if lay.type() == QgsMapLayerType.RasterLayer:
                rasters.append(lay)
        if len(rasters) > 0:
            idx = checked_list.index(rasters[0])
        else:
            idx = -1

        return idx, rasters

    def _make_file_name(self, prn_fmt, scale):
        currtime = time.localtime()
        date=time.strftime('%Y-%m-%d',currtime)
        f_name = date + '_3map_ID###_@@@@@@_' + prn_fmt + '_m' + str(scale)

        return f_name

    def name(self):
        return 'Create atlas'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/grid.png')

    def displayName(self):
        return self.name()

    def group(self):
        return self.groupId()

    def groupId(self):
        return ''

    def createInstance(self):
        return CreateAtlasProcessingAlgorithm()
