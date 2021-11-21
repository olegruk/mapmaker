# -*- coding: utf-8 -*-

import processing
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication
import os.path

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the dialog
from .rectangleAreaTool import RectangleAreaTool
from .mapmaker_processing_provider import mapMakerProcessingProvider
from .to_UTM import ToUTM

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
        self.mapTool = ToUTM(None, self.iface)
    
        icon = QIcon(os.path.dirname(__file__) + "/to_utm.png")
        self.copyAction = QAction(icon, "Set UTM zone", self.iface.mainWindow())
        self.copyAction.setObjectName('setUTM')
        self.copyAction.triggered.connect(self.startCapture)
        self.copyAction.setCheckable(True)
        #self.iface.addToolBarIcon(self.copyAction)
        self.toolbar.addAction(self.copyAction)
        self.iface.addPluginToMenu(self.menu, self.copyAction)
    
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

        self.canvas.mapToolSet.connect(self.unsetTool)
        self.initProcessing()
        self.first_start = True

    def initProcessing(self):
        self.provider = mapMakerProcessingProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unsetTool(self, tool):
        try:
            if not isinstance(tool, ToUTM):
                self.copyAction.setChecked(False)
                self.mapTool.capture4326 = False
        except Exception:
            pass

    def unload(self):
        self.canvas.unsetMapTool(self.mapTool)
        self.iface.removePluginMenu(self.menu, self.copyAction)
        self.iface.removeToolBarIcon(self.copyAction)
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
        QgsApplication.processingRegistry().removeProvider(self.provider)
        del self.toolbar
        self.mapTool = None

    def startCapture(self):
        self.copyAction.setChecked(True)
        self.canvas.setMapTool(self.mapTool)

    def CreateNamedGrid(self,b):
        if b:
            self.prevMapTool = self.iface.mapCanvas().mapTool()
            self.iface.mapCanvas().setMapTool(self.CreateNamedGridTool)
        else:
            self.iface.mapCanvas().setMapTool(self.prevMapTool)
            self.twodayAction.setChecked(False)

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
            self.twodayAction.setChecked(False)

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
            self.twodayAction.setChecked(False)

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
            self.twodayAction.setChecked(False)

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
            self.twodayAction.setChecked(False)

    def LoadMapII(self, startX, startY, endX, endY):
        if startX == endX and startY == endY:
            return
        extent = '%f,%f,%f,%f'%(startX, endX, startY, endY)
        self.iface.mapCanvas().setMapTool(self.prevMapTool)
        processing.execAlgorithmDialog('mapmaker:Load map',
            {'EXTENT': extent})
        #self.iface.messageBar().pushMessage("", "Layer generation finished.", level=Qgis.Info, duration=4)
