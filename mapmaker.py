# -*- coding: utf-8 -*-

import processing
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication, QgsProject, QgsCoordinateReferenceSystem, Qgis
import os.path

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the dialog
from .rectangleAreaTool import RectangleAreaTool
from .mapmaker_processing_provider import mapMakerProcessingProvider
from .to_UTM import ToUTMTool

class mapMaker:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.menu = "&Mapmaker"
        self.canvas = iface.mapCanvas()
        self.provider = None
        self.first_start = None
        self.toolbar = self.iface.addToolBar('Mapmaker Toolbar')
        self.toolbar.setObjectName('MapmakerToolbar')

    def initGui(self):
        iconToUTM = QIcon(os.path.dirname(__file__) + "/to_utm.png")
        self.toUTMZoneAction = QAction(iconToUTM, "Set UTM zone", self.iface.mainWindow())
        self.toUTMZoneAction.setObjectName('setUTM')
        self.toUTMZoneAction.triggered.connect(self.ToUTMZone)
        self.toUTMZoneAction.setCheckable(True)
        #self.iface.addToolBarIcon(self.toUTMZoneAction)
        self.toolbar.addAction(self.toUTMZoneAction)
        self.iface.addPluginToMenu(self.menu, self.toUTMZoneAction)

        iconPseudoMercatorAction = QIcon(os.path.dirname(__file__) + "/to_3857.png")
        self.PseudoMercatorAction = QAction(iconPseudoMercatorAction, "Set EPSG:3857", self.iface.mainWindow())
        self.PseudoMercatorAction.setObjectName('set3857')
        self.PseudoMercatorAction.triggered.connect(self.ToPseudoMercator)
        self.PseudoMercatorAction.setCheckable(False)
        #self.iface.addToolBarIcon(self.toUTMZoneAction)
        self.toolbar.addAction(self.PseudoMercatorAction)
        self.iface.addPluginToMenu(self.menu, self.PseudoMercatorAction)

        iconNamedGrid = QIcon(os.path.dirname(__file__) + '/namedgrid.png')
        self.NamedGridAction = QAction(iconNamedGrid, "Named grid", self.iface.mainWindow())
        self.NamedGridAction.setObjectName("NamedGrid")
        self.NamedGridAction.triggered.connect(self.CreateNamedGrid)
        self.NamedGridAction.setEnabled(True)
        self.NamedGridAction.setCheckable(True)
        #self.iface.addToolBarIcon(self.NamedGridAction)
        self.toolbar.addAction(self.NamedGridAction)
        self.iface.addPluginToMenu(self.menu, self.NamedGridAction)

        iconAtlasGrid = QIcon(os.path.dirname(__file__) + '/grid.png')
        self.AtlasGridAction = QAction(iconAtlasGrid, "Atlas grid", self.iface.mainWindow())
        self.AtlasGridAction.setObjectName("AtlasGrid")
        self.AtlasGridAction.triggered.connect(self.AtlasGrid)
        self.AtlasGridAction.setEnabled(True)
        self.AtlasGridAction.setCheckable(True)
        #self.iface.addToolBarIcon(self.AtlasGridAction)
        self.toolbar.addAction(self.AtlasGridAction)
        self.iface.addPluginToMenu(self.menu, self.AtlasGridAction)
 
        iconCreateAtlas = QIcon(os.path.dirname(__file__) + '/atlas.png')
        self.CreateAtlasAction = QAction(iconCreateAtlas, "Create atlas", self.iface.mainWindow())
        self.CreateAtlasAction.setObjectName("CreateAtlas")
        self.CreateAtlasAction.triggered.connect(self.CreateAtlas)
        self.CreateAtlasAction.setEnabled(True)
        #self.iface.addToolBarIcon(self.CreateAtlasAction)
        self.toolbar.addAction(self.CreateAtlasAction)
        self.iface.addPluginToMenu(self.menu, self.CreateAtlasAction)
 
        iconToGarmin = QIcon(os.path.dirname(__file__) + '/garmin.png')
        self.ToGarminAction = QAction(iconToGarmin, "Create Garmin map", self.iface.mainWindow())
        self.ToGarminAction.setObjectName("ToGarmin")
        self.ToGarminAction.triggered.connect(self.ToGarmin)
        self.ToGarminAction.setEnabled(True)
        self.ToGarminAction.setCheckable(True)
        #self.iface.addToolBarIcon(self.ToGarminAction)
        self.toolbar.addAction(self.ToGarminAction)
        self.iface.addPluginToMenu(self.menu, self.ToGarminAction)

        iconLoadMap = QIcon(os.path.dirname(__file__) + '/map.png')
        self.LoadMapAction = QAction(iconLoadMap, "Load local map", self.iface.mainWindow())
        self.LoadMapAction.setObjectName("LoadMap")
        self.LoadMapAction.triggered.connect(self.LoadMap)
        self.LoadMapAction.setEnabled(True)
        self.LoadMapAction.setCheckable(True)
        #self.iface.addToolBarIcon(self.LoadMapAction)
        self.toolbar.addAction(self.LoadMapAction)
        self.iface.addPluginToMenu(self.menu, self.LoadMapAction)
 
        iconPasteImage = QIcon(os.path.dirname(__file__) + '/1980.png')
        self.PasteImageAction = QAction(iconPasteImage, "Paste image", self.iface.mainWindow())
        self.PasteImageAction.setObjectName("PasteImage")
        self.PasteImageAction.triggered.connect(self.PasteImage)
        self.PasteImageAction.setEnabled(True)
        self.PasteImageAction.setCheckable(True)
        #self.iface.addToolBarIcon(self.PasteImageAction)
        self.toolbar.addAction(self.PasteImageAction)
        self.iface.addPluginToMenu(self.menu, self.PasteImageAction)
 
        iconTracksToPolygons = QIcon(os.path.dirname(__file__) + '/polygon.png')
        self.TracksToPolygonsAction = QAction(iconTracksToPolygons, "Tracks to polygons", self.iface.mainWindow())
        self.TracksToPolygonsAction.setObjectName("TracksToPolygons")
        self.TracksToPolygonsAction.triggered.connect(self.TracksToPolygons)
        self.TracksToPolygonsAction.setEnabled(True)
        #self.iface.addToolBarIcon(self.TracksToPolygonsAction)
        self.toolbar.addAction(self.TracksToPolygonsAction)
        self.iface.addPluginToMenu(self.menu, self.TracksToPolygonsAction)

        iconSetMarker = QIcon(os.path.dirname(__file__) + '/setmarker.png')
        self.SetMarkerAction = QAction(iconSetMarker, "Set km markers", self.iface.mainWindow())
        self.SetMarkerAction.setObjectName("SetKmMarkers")
        self.SetMarkerAction.triggered.connect(self.SetMarker)
        self.SetMarkerAction.setEnabled(True)
        #self.iface.addToolBarIcon(self.TracksToPolygonsAction)
        self.toolbar.addAction(self.SetMarkerAction)
        self.iface.addPluginToMenu(self.menu, self.SetMarkerAction)

        self.toUTMZoneTool = ToUTMTool(self.iface.mapCanvas(), self.toUTMZoneAction)
        self.toUTMZoneTool.detectedZone.connect(self.ToUTMZoneII)
        self.CreateNamedGridTool = RectangleAreaTool(self.iface.mapCanvas(), self.NamedGridAction)
        self.CreateNamedGridTool.rectangleCreated.connect(self.CreateNamedGridII)
        self.AtlasGridTool = RectangleAreaTool(self.iface.mapCanvas(), self.AtlasGridAction)
        self.AtlasGridTool.rectangleCreated.connect(self.AtlasGridII)
        self.PasteImageTool = RectangleAreaTool(self.iface.mapCanvas(), self.PasteImageAction)
        self.PasteImageTool.rectangleCreated.connect(self.PasteImageII)
        self.ToGarminTool = RectangleAreaTool(self.iface.mapCanvas(), self.ToGarminAction)
        self.ToGarminTool.rectangleCreated.connect(self.ToGarminII)
        self.LoadMapTool = RectangleAreaTool(self.iface.mapCanvas(), self.LoadMapAction)
        self.LoadMapTool.rectangleCreated.connect(self.LoadMapII)

        self.initProcessing()
        self.first_start = True

    def initProcessing(self):
        self.provider = mapMakerProcessingProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        self.canvas.unsetMapTool(self.toUTMZoneTool)
        self.iface.removePluginMenu(self.menu, self.toUTMZoneAction)
        self.iface.removeToolBarIcon(self.toUTMZoneAction)
        self.iface.removePluginMenu(self.menu, self.PseudoMercatorAction)
        self.iface.removeToolBarIcon(self.PseudoMercatorAction)
        self.iface.removePluginMenu(self.menu, self.TracksToPolygonsAction)
        self.iface.removeToolBarIcon(self.TracksToPolygonsAction)
        self.iface.removePluginMenu(self.menu, self.PasteImageAction)
        self.iface.removeToolBarIcon(self.PasteImageAction)
        self.iface.removePluginMenu(self.menu, self.NamedGridAction)
        self.iface.removeToolBarIcon(self.NamedGridAction)
        self.iface.removePluginMenu(self.menu, self.AtlasGridAction)
        self.iface.removeToolBarIcon(self.AtlasGridAction)
        self.iface.removePluginMenu(self.menu, self.CreateAtlasAction)
        self.iface.removeToolBarIcon(self.CreateAtlasAction)
        self.iface.removePluginMenu(self.menu, self.ToGarminAction)
        self.iface.removeToolBarIcon(self.ToGarminAction)
        self.iface.removePluginMenu(self.menu, self.LoadMapAction)
        self.iface.removeToolBarIcon(self.LoadMapAction)
        self.iface.removePluginMenu(self.menu, self.SetMarkerAction)
        self.iface.removeToolBarIcon(self.SetMarkerAction)
        QgsApplication.processingRegistry().removeProvider(self.provider)
        del self.toolbar

    def ToUTMZone(self,b):
        if b:
            self.prevMapTool = self.iface.mapCanvas().mapTool()
            self.iface.mapCanvas().setMapTool(self.toUTMZoneTool)
        else:
            self.iface.mapCanvas().setMapTool(self.prevMapTool)
            self.toUTMZoneAction.setChecked(False)

    def ToUTMZoneII(self,zone, crs_string):
        if crs_string is not None:
            self.iface.messageBar().pushMessage("", "The defined zone is {}. New CRS is {}.".format(zone, crs_string), level=Qgis.Info, duration=4)
            dest_crs = QgsCoordinateReferenceSystem(crs_string)
            QgsProject.instance().setCrs(dest_crs)
        self.iface.mapCanvas().setMapTool(self.prevMapTool)

    def ToPseudoMercator(self):
        epsg3857 = QgsCoordinateReferenceSystem('EPSG:3857')
        QgsProject.instance().setCrs(epsg3857)

    def CreateNamedGrid(self,b):
        if b:
            self.prevMapTool = self.iface.mapCanvas().mapTool()
            self.iface.mapCanvas().setMapTool(self.CreateNamedGridTool)
        else:
            self.iface.mapCanvas().setMapTool(self.prevMapTool)
            self.NamedGridAction.setChecked(False)

    def CreateNamedGridII(self, startX, startY, endX, endY):
        if startX == endX and startY == endY:
            return
        extent = '%f,%f,%f,%f'%(startX, endX, startY, endY)
        self.iface.mapCanvas().setMapTool(self.prevMapTool)
        processing.execAlgorithmDialog('mapmaker:Create named grid',
            {'EXTENT': extent})

    def AtlasGrid(self,b):
        if b:
            self.prevMapTool = self.iface.mapCanvas().mapTool()
            self.iface.mapCanvas().setMapTool(self.AtlasGridTool)
        else:
            self.iface.mapCanvas().setMapTool(self.prevMapTool)
            self.AtlasGridAction.setChecked(False)

    def AtlasGridII(self, startX, startY, endX, endY):
        if startX == endX and startY == endY:
            return
        extent = '%f,%f,%f,%f'%(startX, endX, startY, endY)
        self.iface.mapCanvas().setMapTool(self.prevMapTool)
        processing.execAlgorithmDialog('mapmaker:Atlas grid',
            {'EXTENT': extent})
        #self.iface.messageBar().pushMessage("", "Layer generation finished.", level=Qgis.Info, duration=4)

    def CreateAtlas(self):
        processing.execAlgorithmDialog('mapmaker:Create atlas', {})
        
    def TracksToPolygons(self):
        processing.execAlgorithmDialog('mapmaker:Tracks to polygons', {})
        
    def PasteImage(self,b):
        if b:
            self.prevMapTool = self.iface.mapCanvas().mapTool()
            self.iface.mapCanvas().setMapTool(self.PasteImageTool)
        else:
            self.iface.mapCanvas().setMapTool(self.prevMapTool)
            self.PasteImageAction.setChecked(False)

    def PasteImageII(self, startX, startY, endX, endY):
        if startX == endX and startY == endY:
            return
        extent = '%f,%f,%f,%f'%(startX, endX, startY, endY)
        self.iface.mapCanvas().setMapTool(self.prevMapTool)
        processing.execAlgorithmDialog('mapmaker:Paste image',
            {'EXTENT': extent})
        #self.iface.messageBar().pushMessage("", "Layer generation finished.", level=Qgis.Info, duration=4)
     
    def ToGarmin(self,b):
        if b:
            self.prevMapTool = self.iface.mapCanvas().mapTool()
            self.iface.mapCanvas().setMapTool(self.ToGarminTool)
        else:
            self.iface.mapCanvas().setMapTool(self.prevMapTool)
            self.ToGarminAction.setChecked(False)

    def ToGarminII(self, startX, startY, endX, endY):
        if startX == endX and startY == endY:
            return
        extent = '%f,%f,%f,%f'%(startX, endX, startY, endY)
        self.iface.mapCanvas().setMapTool(self.prevMapTool)
        processing.execAlgorithmDialog('mapmaker:Create Garmin map',
            {'EXTENT': extent})
        #self.iface.messageBar().pushMessage("", "Layer generation finished.", level=Qgis.Info, duration=4)
        
    def LoadMap(self,b):
        if b:
            self.prevMapTool = self.iface.mapCanvas().mapTool()
            self.iface.mapCanvas().setMapTool(self.LoadMapTool)
        else:
            self.iface.mapCanvas().setMapTool(self.prevMapTool)
            self.LoadMapAction.setChecked(False)

    def LoadMapII(self, startX, startY, endX, endY):
        if startX == endX and startY == endY:
            return
        extent = '%f,%f,%f,%f'%(startX, endX, startY, endY)
        self.iface.mapCanvas().setMapTool(self.prevMapTool)
        processing.execAlgorithmDialog('mapmaker:Load map',
            {'EXTENT': extent})
        #self.iface.messageBar().pushMessage("", "Layer generation finished.", level=Qgis.Info, duration=4)

    def SetMarker(self):
        processing.execAlgorithmDialog('mapmaker:Set km markers', {})
