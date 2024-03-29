# -*- coding: utf-8 -*-

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QRectF
from qgis.core import (QgsProcessingException,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterEnum,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFileDestination,
                       QgsRasterLayer,
                       QgsProject,
                       QgsPrintLayout,
                       QgsLayoutItemMap,
                       QgsLayoutExporter,
                       QgsLayoutSize,
                       QgsLayerTreeLayer,
                       QgsCoordinateReferenceSystem)

from osgeo import gdal
import os.path

class LoadMapProcessingAlgorithm(QgsProcessingAlgorithm):

    EXTENT = 'EXTENT'
    SCALE = 'SCALE'
    FILE = 'FILE'
    BRIGHT = 'BRIGHT'
    ZOOM = 'ZOOM'
    RASTER = 'RASTER'

    def initAlgorithm(self, config=None):
        self.zoomlist = ['z0', 'z1', 'z2', 'z3', 'z4', 'z5', 'z6', 'z7', 'z8', 'z9', 'z10', 'z11', 'z12', 'z13', 'z14', 'z15', 'z16', 'z17', 'z18', 'z19', 'z20', 'z21', 'z22', 'z23', 'z24']
        self.addParameter(QgsProcessingParameterEnum(self.ZOOM, 'Map zoom', self.zoomlist, defaultValue=16))
        self.addParameter(QgsProcessingParameterNumber(self.BRIGHT, 'Map brightness:', defaultValue=0, optional=False, minValue=0, maxValue=10000))
        self.addParameter(QgsProcessingParameterExtent(self.EXTENT, 'Map extent'))
        self.addParameter(QgsProcessingParameterFileDestination(self.FILE, 'Local map file', '*.tif', defaultValue=''))
        
    def processAlgorithm(self, parameters, context, feedback):

        curr_crs = context.project().crs()

        #switch to WGS84 / Pseudo-Mercator
        crs = QgsCoordinateReferenceSystem('EPSG:3857')
        QgsProject.instance().setCrs(crs)
        SourceCRS = str(crs.authid())

        zoom = self.parameterAsEnum(parameters, self.ZOOM, context)
        bright = self.parameterAsInt(parameters, self.BRIGHT, context)
        bbox = self.parameterAsExtent(parameters, self.EXTENT, context, crs)
        #bbox_geom = self.parameterAsExtentGeometry(parameters, self.EXTENT, context, crs)
        input_file = self.parameterAsFile(parameters, self.FILE, context)
        
        maxZoomLevel = 24
        scale_list = [round(1774976128 / (2 ** i)) for i in range(maxZoomLevel)]
        mupp_list = [40075016.685 / (2 ** i * 256) for i in range(maxZoomLevel)]
        scale = scale_list[zoom]
        mpp = mupp_list[zoom]

        height_m = int(round(bbox.width()))
        width_m = int(round(bbox.height()))
        
        height = int(round((height_m/scale)*1000)) #height of "paper" in mm
        width = int(round((width_m/scale)*1000))
        
        height_pix = int(round(height_m/mpp)) #height of picture in pix
        width_pix = int(round(width_m/mpp))
        
        dpi_w = int(round((25.4*width_m)/(width*mpp)))
        
        root = QgsProject.instance().layerTreeRoot()
        layer_list = root.checkedLayers()
        idx = self._last_raster(layer_list)
        layer_list[idx].brightnessFilter().setBrightness(bright)
                
        QgsProject.instance().addMapLayers(layer_list)

        self.layout = QgsPrintLayout(QgsProject.instance())
        self.layout.initializeDefaults()
        page = self.layout.pageCollection().pages()[0]
        page.setPageSize(QgsLayoutSize(height, width))

        self.atlas_map = QgsLayoutItemMap(self.layout)
        self.atlas_map.attemptSetSceneRect(QRectF(0, 0, height+1, width+1))
        self.atlas_map.setFrameEnabled(False)
        self.atlas_map.setScale(scale)
        self.atlas_map.setLayers(layer_list)
        self.layout.addLayoutItem(self.atlas_map)
        self.atlas_map.setExtent(bbox)
 
        exporter = QgsLayoutExporter(self.layout)
        export_settings = QgsLayoutExporter.ImageExportSettings()
        export_settings.dpi = dpi_w
        if os.path.isfile(input_file):
            try:
                os.remove(input_file)
            except OSError:
                QgsProject.instance().setCrs(curr_crs)
                raise QgsProcessingException('Unable to overwrite %s. File locked by another application.' %(input_file))
        exporter.exportToImage(input_file, export_settings)
        exporter.georeferenceOutput(file = input_file, referenceMap = self.atlas_map, dpi = dpi_w)
        
        # Set Geotransform values
        pic_x_min = bbox.xMinimum()
        pic_y_min = bbox.yMinimum()
        pic_x_max = bbox.xMaximum()
        pic_y_max = bbox.yMaximum()
        xScale = (pic_x_max - pic_x_min) / height_pix
        yScale = (pic_y_min - pic_y_max) / width_pix
        input_dataset = gdal.Open(input_file)
        input_dataset.SetGeoTransform([pic_x_min, xScale, 0, pic_y_max, 0, yScale])
        input_dataset.SetProjection(SourceCRS)
        input_dataset = None
        layer_name = layer_list[idx].name() + ' - Local'
        new_layer = QgsRasterLayer(input_file, layer_name)
        if not new_layer.isValid():
            QgsProject.instance().setCrs(curr_crs)
            raise QgsProcessingException('Layer %s failed to load!' %(input_file))
        QgsProject.instance().addMapLayer(new_layer)
        root.insertChildNode(0, QgsLayerTreeLayer(new_layer))
        QgsProject.instance().setCrs(curr_crs)
        return {"OUTPUT": [idx, layer_list[idx].name(), layer_list]}

    def _last_raster (self, checked_list):
        rasters = []
        for lay in checked_list:
            if lay.dataProvider().name() == 'wms':
                rasters.append(lay)
        if len(rasters) > 0:
            idx = checked_list.index(rasters[0])
        else:
            idx = 0
        
        return idx
    
    def name(self):
        return 'Load map'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/map.png')

    def displayName(self):
        return self.name()

    def group(self):
        return self.groupId()

    def groupId(self):
        return ''

    def createInstance(self):
        return LoadMapProcessingAlgorithm()
