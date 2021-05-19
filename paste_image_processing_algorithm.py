# -*- coding: utf-8 -*-

from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessingException,
                       QgsProcessingParameterExtent,
                       QgsProcessingAlgorithm,
                       QgsRasterLayer,
                       QgsProject,
                       QgsLayerTreeLayer,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber)
from processing.core.Processing import Processing
import os.path
from osgeo import gdal

class PasteImageProcessingAlgorithm(QgsProcessingAlgorithm):

    EXTENT = 'EXTENT'
    FILE = 'FILE'
    OUTPUT = 'OUTPUT'
    BRIGHT = 'BRIGHT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterExtent(self.EXTENT, 'Image extent'))
        self.addParameter(QgsProcessingParameterFile(self.FILE, 'Image file', extension='png'))
        self.addParameter(QgsProcessingParameterNumber(self.BRIGHT, 'Image brightness:', defaultValue=-130, optional=False, minValue=-500, maxValue=500))
        
    def processAlgorithm(self, parameters, context, feedback):
        Processing.initialize()

        crs = context.project().crs()
        SourceCRS = str(crs.authid())
        bbox = self.parameterAsExtent(parameters, self.EXTENT, context, crs)
        input_file = self.parameterAsFile(parameters, self.FILE, context)
        bright = self.parameterAsInt(parameters, self.BRIGHT, context)

        input_dataset = gdal.Open(input_file)

        x_min = bbox.xMinimum()
        y_min = bbox.yMinimum()
        x_max = bbox.xMaximum()
        y_max = bbox.yMaximum()
        
        x_extent = input_dataset.RasterXSize
        y_extent = input_dataset.RasterYSize

        xScale = (x_max - x_min) / x_extent
        yScale = (y_min - y_max) / y_extent

        input_dataset = gdal.Open(input_file)
        input_dataset.SetGeoTransform([x_min, xScale, 0, y_max, 0, yScale])
        input_dataset.SetProjection(SourceCRS)

        input_dataset = None

        new_layer = QgsRasterLayer(input_file, 'Logo')
        if not new_layer.isValid():
            raise QgsProcessingException('Layer %s failed to load!' %(input_file))
        QgsProject.instance().addMapLayer(new_layer)
        root = QgsProject.instance().layerTreeRoot()
        root.insertChildNode(0, QgsLayerTreeLayer(new_layer))
        new_layer.brightnessFilter().setBrightness(bright)

        return {"OUTPUT": input_file}

    def name(self):
        return 'Paste image'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/1980.png')

    def displayName(self):
        return self.name()

    def group(self):
        return self.groupId()

    def groupId(self):
        return ''

    def createInstance(self):
        return PasteImageProcessingAlgorithm()
