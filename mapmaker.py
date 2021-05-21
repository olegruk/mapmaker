# -*- coding: utf-8 -*-

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtXml import QDomDocument
from qgis.core import QgsApplication, QgsProject, QgsVectorLayer, QgsReadWriteContext, Qgis
import processing, os.path, traceback

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the dialog
from .mapmaker_processing_provider import mapMakerProcessingProvider
from .to_UTM import ToUTM

class mapMaker:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
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
        self.iface.addPluginToMenu("&Mapmaker", self.copyAction)
    
        iconTracksToPolygons = QIcon(os.path.dirname(__file__) + '/polygon.png')
        self.TracksToPolygonsAction = QAction(iconTracksToPolygons, "Tracks to polygons", self.iface.mainWindow())
        self.TracksToPolygonsAction.setObjectName("TracksToPolygons")
        self.TracksToPolygonsAction.triggered.connect(self.TracksToPolygons)
        self.TracksToPolygonsAction.setEnabled(True)
        #self.iface.addToolBarIcon(self.TracksToPolygonsAction)
        self.toolbar.addAction(self.TracksToPolygonsAction)
        self.iface.addPluginToMenu('&Mapmaker', self.TracksToPolygonsAction)

        iconPasteImage = QIcon(os.path.dirname(__file__) + '/1980.png')
        self.PasteImageAction = QAction(iconPasteImage, "Paste image", self.iface.mainWindow())
        self.PasteImageAction.setObjectName("PasteImage")
        self.PasteImageAction.triggered.connect(self.PasteImage)
        self.PasteImageAction.setEnabled(True)
        #self.iface.addToolBarIcon(self.PasteImageAction)
        self.toolbar.addAction(self.PasteImageAction)
        self.iface.addPluginToMenu('&Mapmaker', self.PasteImageAction)
 
        iconNamedGrid = QIcon(os.path.dirname(__file__) + '/namedgrid.png')
        self.NamedGridAction = QAction(iconNamedGrid, "Named grid", self.iface.mainWindow())
        self.NamedGridAction.setObjectName("NamedGrid")
        self.NamedGridAction.triggered.connect(self.CreateNamedGrid)
        self.NamedGridAction.setEnabled(True)
        #self.iface.addToolBarIcon(self.NamedGridAction)
        self.toolbar.addAction(self.NamedGridAction)
        self.iface.addPluginToMenu('&Mapmaker', self.NamedGridAction)

        iconAtlasGrid = QIcon(os.path.dirname(__file__) + '/grid.png')
        self.AtlasGridAction = QAction(iconAtlasGrid, "Atlas grid", self.iface.mainWindow())
        self.AtlasGridAction.setObjectName("AtlasGrid")
        self.AtlasGridAction.triggered.connect(self.AtlasGrid)
        self.AtlasGridAction.setEnabled(True)
        #self.iface.addToolBarIcon(self.AtlasGridAction)
        self.toolbar.addAction(self.AtlasGridAction)
        self.iface.addPluginToMenu('&Mapmaker', self.AtlasGridAction)
 
        iconCreateAtlas = QIcon(os.path.dirname(__file__) + '/atlas.png')
        self.CreateAtlasAction = QAction(iconCreateAtlas, "Create atlas", self.iface.mainWindow())
        self.CreateAtlasAction.setObjectName("CreateAtlas")
        self.CreateAtlasAction.triggered.connect(self.CreateAtlas)
        self.CreateAtlasAction.setEnabled(True)
        #self.iface.addToolBarIcon(self.CreateAtlasAction)
        self.toolbar.addAction(self.CreateAtlasAction)
        self.iface.addPluginToMenu('&Mapmaker', self.CreateAtlasAction)
 
        iconToGarmin = QIcon(os.path.dirname(__file__) + '/garmin.png')
        self.ToGarminAction = QAction(iconToGarmin, "Create Garmin map", self.iface.mainWindow())
        self.ToGarminAction.setObjectName("ToGarmin")
        self.ToGarminAction.triggered.connect(self.ToGarmin)
        self.ToGarminAction.setEnabled(True)
        #self.iface.addToolBarIcon(self.ToGarminAction)
        self.toolbar.addAction(self.ToGarminAction)
        self.iface.addPluginToMenu('&Mapmaker', self.ToGarminAction)

        iconLoadMap = QIcon(os.path.dirname(__file__) + '/map.png')
        self.LoadMapAction = QAction(iconLoadMap, "Load local map", self.iface.mainWindow())
        self.LoadMapAction.setObjectName("LoadMap")
        self.LoadMapAction.triggered.connect(self.LoadMap)
        self.LoadMapAction.setEnabled(True)
        #self.iface.addToolBarIcon(self.LoadMapAction)
        self.toolbar.addAction(self.LoadMapAction)
        self.iface.addPluginToMenu('&Mapmaker', self.LoadMapAction)
 
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
        self.iface.removePluginMenu('&Mapmaker', self.copyAction)
        self.iface.removeToolBarIcon(self.copyAction)
        self.iface.removePluginMenu('&Mapmaker', self.TracksToPolygonsAction)
        self.iface.removeToolBarIcon(self.TracksToPolygonsAction)
        self.iface.removePluginMenu('&Mapmaker', self.PasteImageAction)
        self.iface.removeToolBarIcon(self.PasteImageAction)
        self.iface.removePluginMenu('&Mapmaker', self.NamedGridAction)
        self.iface.removeToolBarIcon(self.NamedGridAction)
        self.iface.removePluginMenu('&Mapmaker', self.AtlasGridAction)
        self.iface.removeToolBarIcon(self.AtlasGridAction)
        self.iface.removePluginMenu('&Mapmaker', self.CreateAtlasAction)
        self.iface.removeToolBarIcon(self.CreateAtlasAction)
        self.iface.removePluginMenu('&Mapmaker', self.ToGarminAction)
        self.iface.removeToolBarIcon(self.ToGarminAction)
        self.iface.removePluginMenu('&Mapmaker', self.LoadMapAction)
        self.iface.removeToolBarIcon(self.LoadMapAction)
        QgsApplication.processingRegistry().removeProvider(self.provider)
        del self.toolbar
        self.mapTool = None

    def startCapture(self):
        self.copyAction.setChecked(True)
        self.canvas.setMapTool(self.mapTool)

    def CreateNamedGrid(self):
        processing.execAlgorithmDialog('mapmaker:Create named grid', {})

    def AtlasGrid(self):
        processing.execAlgorithmDialog('mapmaker:Atlas grid', {})

    def CreateAtlas(self):
        processing.execAlgorithmDialog('mapmaker:Create atlas', {})
        
    def TracksToPolygons(self):
        processing.execAlgorithmDialog('mapmaker:Tracks to polygons', {})
        
    def PasteImage(self):
        processing.execAlgorithmDialog('mapmaker:Paste image', {})
     
    def ToGarmin(self):
        processing.execAlgorithmDialog('mapmaker:Create Garmin map', {})
        
    def LoadMap(self):
        processing.execAlgorithmDialog('mapmaker:Load map', {})