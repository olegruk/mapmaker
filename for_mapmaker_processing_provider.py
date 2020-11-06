# -*- coding: utf-8 -*-

"""
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
from qgis.core import QgsProcessingProvider
from .named_grid_processing_algorithm import NamedGridProcessingAlgorithm
from .atlas_grid_processing_algorithm import AtlasGridProcessingAlgorithm
from .create_atlas_processing_algorithm import CreateAtlasProcessingAlgorithm
from .tracks_to_polygons_processing_algorithm import TracksToPolygonsProcessingAlgorithm
from .paste_image_processing_algorithm import PasteImageProcessingAlgorithm
from .to_garmin_processing_algorithm import ToGarminProcessingAlgorithm
from .load_map_processing_algorithm import LoadMapProcessingAlgorithm

import os.path

class forMapMakerProcessingProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self):
        pass

    def loadAlgorithms(self):
        self.addAlgorithm(NamedGridProcessingAlgorithm())
        self.addAlgorithm(AtlasGridProcessingAlgorithm())
        self.addAlgorithm(CreateAtlasProcessingAlgorithm())
        self.addAlgorithm(TracksToPolygonsProcessingAlgorithm())
        self.addAlgorithm(PasteImageProcessingAlgorithm())
        self.addAlgorithm(ToGarminProcessingAlgorithm())
        self.addAlgorithm(LoadMapProcessingAlgorithm())

    def id(self):
        return 'for_mapmaker'

    def name(self):
        return 'For mapmaker'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icon.png')

    def longName(self):
        return self.name()
