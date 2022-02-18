# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject, QgsSettings, QgsMessageLog
from qgis.gui import QgsVertexMarker, QgsMapTool

class ToUTMTool(QgsMapTool):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    detectedZone = pyqtSignal(int, str)

    def __init__(self, canvas, action):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.active = False
        self.setAction(action)
        self.capture4326 = False

    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        self.snapcolor = QgsSettings().value( "/qgis/digitizing/snap_color" , QColor( Qt.magenta ) )

    def deactivate(self):
        QgsMapTool.deactivate(self)

    def canvasReleaseEvent(self, event):
        '''Capture the coordinate when the mouse button has been released,
        format it, and copy it to the clipboard. pt is QgsPointXY'''
        pt = self.snappoint(event.originalPixelPoint())
        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        try:
            if self.capture4326:
                canvasCRS = self.canvas.mapSettings().destinationCrs()
                transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
                pt4326 = transform.transform(pt.x(), pt.y())
                return
            pt4326 = self.ConvertCoord(pt)
            zone, crs_string = self._define_grid_crs(pt4326)
            self.detectedZone.emit(zone, crs_string)
        except Exception as e:
            QgsMessageLog.logMessage("Invalid coordinate: {}".format(e), "MapMaker")
            
    def snappoint(self, point):
        # point - QPoint
        match = self.canvas.snappingUtils().snapToMap(point)
        if match.isValid():
            if self.vertex is None:
                self.vertex = QgsVertexMarker(self.canvas)
                self.vertex.setIconSize(12)
                self.vertex.setPenWidth(2)
                self.vertex.setColor(self.snapcolor)
                self.vertex.setIconType(QgsVertexMarker.ICON_BOX)
            self.vertex.setCenter(match.point())
            return (match.point())
        else:
            return self.toMapCoordinates(point)

    def ConvertCoord(self, pt):
        '''Format the coordinate string.'''
        # ProjectionTypeWgs84
        # Make sure the coordinate is transformed to EPSG:4326
        canvasCRS = self.canvas.mapSettings().destinationCrs()
        epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')
        if canvasCRS == epsg4326:
            pt4326 = pt
        else:
            transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
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
   
        return zone, new_crs_str

