from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import Qgis, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsPointXY, QgsProject, QgsSettings
from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker

class ToUTM(QgsMapToolEmitPoint):
    '''Class to interact with the map canvas to capture the coordinate
    when the mouse button is pressed and to display the coordinate in
    in the status bar.'''
    capturesig = pyqtSignal(QgsPointXY)

    def __init__(self, settings, iface):
        QgsMapToolEmitPoint.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.capture4326 = False

    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        self.snapcolor = QgsSettings().value( "/qgis/digitizing/snap_color" , QColor( Qt.magenta ) )

    def deactivate(self):
        pass

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
                self.capturesig.emit(pt4326)
                return
            pt4326 = self.ConvertCoord(pt)
            zone, crs_string = self._define_grid_crs(pt4326)
            if crs_string is not None:
                self.iface.messageBar().pushMessage("", "The defined zone is {}. New CRS is {}.".format(zone, crs_string), level=Qgis.Info, duration=4)
                dest_crs = QgsCoordinateReferenceSystem(crs_string)
                QgsProject.instance().setCrs(dest_crs)
        except Exception as e:
            self.iface.messageBar().pushMessage("", "Invalid coordinate: {}".format(e), level=Qgis.Warning, duration=4)
            
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
            return (match.point()) # Returns QgsPointXY
        else:
            return self.toMapCoordinates(point) # QPoint input, returns QgsPointXY

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

