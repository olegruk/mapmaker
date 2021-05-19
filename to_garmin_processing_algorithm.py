# -*- coding: utf-8 -*-

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QRectF
from qgis.core import (QgsPointXY,
                       QgsProcessingException,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterEnum,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterScale,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsPrintLayout,
                       QgsLayoutItemMap,
                       QgsLayoutExporter,
                       QgsLayoutSize,
                       QgsMapLayerType)

from osgeo import gdal
from osgeo import gdalconst

import zipfile
import tempfile
import os.path

class ToGarminProcessingAlgorithm(QgsProcessingAlgorithm):

    EXTENT = 'EXTENT'
    SCALE = 'SCALE'
    FILE = 'FILE'
    BRIGHT = 'BRIGHT'
    ZOOM = 'ZOOM'

    def initAlgorithm(self, config=None):
        self.zoomlist = ['z24', 'z23', 'z22', 'z21', 'z20', 'z19', 'z18', 'z17', 'z16', 'z15', 'z14', 'z13', 'z12', 'z11', 'z10', 'z9', 'z8', 'z7', 'z6', 'z5', 'z4', 'z3', 'z2', 'z1']
        self.addParameter(QgsProcessingParameterEnum(self.ZOOM, 'Map zoom', self.zoomlist, defaultValue=8))
        self.addParameter(QgsProcessingParameterScale(self.SCALE, 'Map scale'))
        #self.addParameter(QgsProcessingParameterNumber(self.SCALE, 'Map scale:', defaultValue=250, optional=False, minValue=1, maxValue=6000000))
        self.addParameter(QgsProcessingParameterNumber(self.BRIGHT, 'Map brightness:', defaultValue=0, optional=False, minValue=0, maxValue=10000))
        self.addParameter(QgsProcessingParameterExtent(self.EXTENT, 'Map extent'))
        self.addParameter(QgsProcessingParameterFileDestination(self.FILE, 'Map output file', '*.kmz', defaultValue=''))

    def processAlgorithm(self, parameters, context, feedback):

        feedback.setProgress(0)
        curr_crs = context.project().crs()

        #switch to WGS84 / Pseudo-Mercator
        crs = QgsCoordinateReferenceSystem('EPSG:3857')
        QgsProject.instance().setCrs(crs)
        SourceCRS = str(crs.authid())

        #scale = self.parameterAsInt(parameters, self.SCALE, context)
        zoom = 'z' + str(24 - self.parameterAsEnum(parameters, self.ZOOM, context))
        bright = self.parameterAsInt(parameters, self.BRIGHT, context)
        bbox = self.parameterAsExtent(parameters, self.EXTENT, context, crs)
        bbox_geom = self.parameterAsExtentGeometry(parameters, self.EXTENT, context, crs)
        kmz_file = self.parameterAsFile(parameters, self.FILE, context)
        real_scale = int(self.parameterAsDouble(parameters, self.SCALE, context))
        
        zoom_dict = {'z1':591657528, 'z2':195828764, 'z3':147914382, 'z4':73957191, 'z5':36978595, 'z6':18489298, 'z7':9244649, 'z8':4622324, 'z9':2311162, 'z10':1155581, 'z11':577791, 'z12':288895, 'z13':144448, 'z14':72224, 'z15':36112, 'z16':18056, 'z17':9028, 'z18':4514, 'z19':2257, 'z20':1128, 'z21':564, 'z22':282, 'z23':141, 'z24':71}
        mpp_dict = {'z1':88958.05, 'z2':44479.02, 'z3':22239.51, 'z4':11119.76, 'z5':5517.85, 'z6':2757.18, 'z7':1378.59, 'z8':691.2, 'z9':345.6, 'z10':172.8, 'z11':86.4, 'z12':43.2, 'z13':21.6, 'z14':10.8, 'z15':5.4, 'z16':2.7, 'z17':1.35, 'z18':0.67, 'z19':0.34, 'z20':0.17, 'z21':0.08, 'z22':0.04, 'z23':0.02, 'z24':0.01}
        if real_scale > 0:
            scale = real_scale
            for i,z in zoom_dict.items():
                if z >= scale:
                    zoom = i
                else:
                    break
        else:
            scale = zoom_dict[zoom]
        mpp = mpp_dict[zoom]

        # Create tmp-folder
        in_file = os.path.basename(kmz_file[0:(len(kmz_file) - 4)])
        out_folder = tempfile.mkdtemp('_tmp', 'fmm_')
        out_put = os.path.join(out_folder, in_file)
        input_file = out_put + u'.png'
        tname = in_file

        height_m = int(round(bbox.width()))
        width_m = int(round(bbox.height()))

        height = int(round((height_m/scale)*1000)) #height of "paper" in mm
        width = int(round((width_m/scale)*1000))

        height_pix = int(round(height_m/mpp)) #height of picture in pix
        width_pix = int(round(width_m/mpp))

        dpi_w = int(round((25.4*width_m)/(width*mpp)))
        dpi_h = int(round((25.4*height_m)/(height*mpp)))

        root = QgsProject.instance().layerTreeRoot()
        layer_list = root.checkedLayers()
        idx = self._last_raster(layer_list)
        if idx >= 0:
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

        feedback.setProgress(1)

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

        if idx >= 0:
            layer_list[idx].brightnessFilter().setBrightness(0)

        feedback.setProgress(20)

        # Set variables
        optimize = 1
        skip_empty = 1
        max_y_ext_general = 1024
        max_x_ext_general = 1024

        # Set options for jpg-production
        options = []
        options.append("QUALITY=95")
        draworder = 30
        max_pix = (1024 * 1024)

        # Set Geotransform values
        pic_x_min = bbox.xMinimum()
        pic_y_min = bbox.yMinimum()
        pic_x_max = bbox.xMaximum()
        pic_y_max = bbox.yMaximum()

        # Calculate tile size and number of tiles
        indataset = gdal.Open(input_file)
        x_extent = indataset.RasterXSize
        y_extent = indataset.RasterYSize

        if optimize == 1 :
            # Identify length of the short and long side of the map canvas and their relation
            short_ext = min(x_extent, y_extent)
            long_ext = max(x_extent, y_extent)
            s_l_side_relation = 0

            # Estimate number of tiles in the result
            if float(x_extent * y_extent) % (1024 * 1024) >= 1:
                expected_tile_n = int(float(x_extent * y_extent) / (1024 * 1024)) + 1
            else:
                expected_tile_n = int(float(x_extent * y_extent) / (1024 * 1024))

            # Find settings for tiling with:
            # 1 minimum number of tiles,
            # 2 a short / long size relation close to 1,
            # 3 and a minimum numer of pixels in each tile
            for tc in range(1, expected_tile_n + 1, 1):
                if expected_tile_n % tc >= 1:
                    continue
                else:

                    if short_ext % tc >= 1:
                        s_pix = int(short_ext / tc) + 1
                    else:
                        s_pix = int(short_ext / tc)

                    if long_ext % tc >= 1:
                        l_pix = int(long_ext / (expected_tile_n / tc)) + 1
                    else:
                        l_pix = int(long_ext / (expected_tile_n / tc))

                    if (s_pix * l_pix) <= (1024 * 1024):
                        if min((float(s_pix) / float(l_pix)), (float(l_pix) / float(s_pix))) >= s_l_side_relation:
                            s_l_side_relation = min((float(s_pix) / float(l_pix)), (float(l_pix) / float(s_pix)))
                            s_pix_opt = s_pix
                            l_pix_opt = l_pix

            # Set tile size variable according to optimal setings
            if short_ext == x_extent:
                max_x_ext_general = s_pix_opt
                max_y_ext_general = l_pix_opt
            else:
                max_y_ext_general = s_pix_opt
                max_x_ext_general = l_pix_opt

        # Identify number of rows and columns
        n_cols_rest = x_extent % max_x_ext_general
        n_rows_rest = y_extent % max_y_ext_general

        if n_cols_rest >= 1:
            n_cols = (x_extent // max_x_ext_general) + 1
        else:
            n_cols = (x_extent // max_x_ext_general)

        if n_rows_rest >= 1:
            n_rows = (y_extent // max_y_ext_general) + 1
        else:
            n_rows = (y_extent // max_y_ext_general)

        # Check if number of tiles is below Garmins limit of 100 tiles (across all custom maps)
        n_tiles = (n_rows * n_cols)
        if n_tiles > 100:
            QgsProject.instance().setCrs(curr_crs)
            raise QgsProcessingException("The number of tiles (%s) is likely to exceed Garmins limit of 100 tiles! Not all tiles will be displayed on your GPS unit. Consider reducing your map size (extend or zoom-factor)." %(n_tiles))

        # Check if size of tiles is below Garmins limit of 1 megapixel (for each tile)
        n_pix = (max_x_ext_general * max_y_ext_general)

        if n_pix > max_pix:
            QgsProject.instance().setCrs(curr_crs)
            raise QgsProcessingException("The number of pixels in a tile (%s) exceeds Garmins limit of 1 megapixel per tile! Images will not be displayed properly." %(n_pix))

        feedback.setProgress(30)
        total = 70.0 / n_tiles

        kmz = zipfile.ZipFile(kmz_file, 'w')
        with open(os.path.join(out_folder, 'doc.kml'), 'w') as kml:

            # Write kml header
            kml.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            kml.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            kml.write('  <Document>\n')
            kml.write('    <name>' + tname.encode('UTF-8').decode('utf-8') + '</name>\n')

            # Produce .jpg tiles using gdal_translate looping through the complete rows and columns (1024x1024 pixel)
            y_offset = 0
            x_offset = 0
            r = 1
            c = 1
            n_tiles = 0
            empty_tiles = 0
            # Loop through rows
            for r in range(1, int(n_rows) + 1, 1):
                # Define maximum Y-extend of tiles
                if r == (n_rows) and n_rows_rest > 0:
                    max_y_ext = n_rows_rest
                else:
                    max_y_ext = max_y_ext_general

                # (Within row-loop) Loop through columns
                for c in range(1, int(n_cols) + 1, 1):
                    # Define maximum X-extend of tiles
                    if c == int(n_cols) and n_cols_rest > 0:
                        max_x_ext = n_cols_rest
                    else:
                        max_x_ext = max_x_ext_general
                    # Define name for tile-jpg
                    t_name = tname + '_%(r)d_%(c)d.jpg' % {"r": r, "c": c}
                    # Set parameters for "gdal_translate" (JPEG-driver has no Create() (but CreateCopy()) method so first a VRT has to be created band by band
                    # Create VRT dataset for tile
                    mem_driver = gdal.GetDriverByName("MEM")
                    mem_driver.Register()
                    t_file = mem_driver.Create('', max_x_ext, max_y_ext, 3, gdalconst.GDT_Byte)
                    t_band_1 = indataset.GetRasterBand(1).ReadAsArray(x_offset, y_offset, max_x_ext, max_y_ext)
                    t_band_2 = indataset.GetRasterBand(2).ReadAsArray(x_offset, y_offset, max_x_ext, max_y_ext)
                    t_band_3 = indataset.GetRasterBand(3).ReadAsArray(x_offset, y_offset, max_x_ext, max_y_ext)

                    if skip_empty == 1 :
                        if t_band_1.min() == 255 and t_band_2.min() == 255 and t_band_3.min() == 255 :
                            empty_tiles = empty_tiles + 1

                    t_file.GetRasterBand(1).WriteArray(t_band_1)
                    t_file.GetRasterBand(2).WriteArray(t_band_2)
                    t_file.GetRasterBand(3).WriteArray(t_band_3)
                    t_band_1 = None
                    t_band_2 = None
                    t_band_3 = None

                    # Translate MEM dataset to JPG
                    jpg_driver = gdal.GetDriverByName("JPEG")
                    jpg_driver.Register()
                    jpg_driver.CreateCopy(os.path.join(out_folder, t_name), t_file, options=options)

                    # Close GDAL-datasets
                    t_file = None
                    # Get bounding box for tile
                    n = pic_y_max - (y_offset * mpp)
                    s = pic_y_max - ((y_offset + max_y_ext) * mpp)
                    e = pic_x_min + ((x_offset + max_x_ext) * mpp)
                    w = pic_x_min + (x_offset * mpp)

                    crsDest = QgsCoordinateReferenceSystem('EPSG:4326')    # WGS 84
                    xform = QgsCoordinateTransform(crs, crsDest, QgsProject.instance())
                    pt1 = xform.transform(QgsPointXY(w,n))
                    pt2 = xform.transform(QgsPointXY(e,s))

                    n4326 = pt1.y()
                    s4326 = pt2.y()
                    e4326 = pt2.x()
                    w4326 = pt1.x()

                    # Add .jpg to .kmz-file and remove it together with its meta-data afterwards
                    kmz.write(os.path.join(out_folder, t_name), t_name)
                    if os.path.exists(os.path.join(out_folder, t_name)) :
                        os.remove(os.path.join(out_folder, t_name))

                    # Write kml-tags for each tile (Name, DrawOrder, JPEG-Reference, GroundOverlay)
                    kml.write('')
                    kml.write('    <GroundOverlay>\n')
                    kml.write('        <name>' + tname.encode('UTF-8').decode('utf-8') + ' Tile ' + str(r) + '_' + str(c) + '</name>\n')
                    kml.write('        <drawOrder>' + str(draworder) + '</drawOrder>\n')
                    kml.write('        <Icon>\n')
                    kml.write('          <href>' + tname.encode('UTF-8').decode('utf-8') + '_' + str(r) + '_' + str(c) + '.jpg</href>\n')  # %{"r":r, "c":c}
                    kml.write('        </Icon>\n')
                    kml.write('        <LatLonBox>\n')
                    kml.write('          <north>' + str(n4326) + '</north>\n')
                    kml.write('          <south>' + str(s4326) + '</south>\n')
                    kml.write('          <east>' + str(e4326) + '</east>\n')
                    kml.write('          <west>' + str(w4326) + '</west>\n')
                    kml.write('        </LatLonBox>\n')
                    kml.write('    </GroundOverlay>\n')

                    # Calculate new X-offset
                    x_offset = (x_offset + max_x_ext)
                    n_tiles = (n_tiles + 1)
                    # Update progress bar
                    feedback.setProgress(30 + int(n_tiles * total))
                # Calculate new Y-offset
                y_offset = (y_offset + max_y_ext)
                # Reset X-offset
                x_offset = 0

            # Write kml footer
            kml.write('  </Document>\n')
            kml.write('</kml>\n')
        # Close kml file
        kml.close()

        # Close GDAL dataset
        indataset = None

        # Add .kml to .kmz-file and remove it together with the rest of the temporary files
        kmz.write(os.path.join(out_folder, u'doc.kml'), u'doc.kml')
        if os.path.exists(os.path.join(out_folder, u'doc.kml')) :
            os.remove(os.path.join(out_folder, u'doc.kml'))
        kmz.close()
        if os.path.exists(input_file) :
            os.remove(input_file)
        if os.path.exists(out_folder) :
            os.rmdir(out_folder)

        tiles_total = n_tiles - empty_tiles
        QgsProject.instance().setCrs(curr_crs)

        return {"OUTPUT": [zoom, scale, tiles_total, layer_list]}

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

        return idx

    def name(self):
        return 'Create Garmin map'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/garmin.png')

    def displayName(self):
        return self.name()

    def group(self):
        return self.groupId()

    def groupId(self):
        return ''

    def createInstance(self):
        return ToGarminProcessingAlgorithm()
