# -*- coding: utf-8 -*-

import os.path
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsWkbTypes,
                       QgsFeatureSink,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)

from processing.core.Processing import Processing

class TracksToPolygonsProcessingAlgorithm(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT, 'Tracks layer', types=[QgsProcessing.TypeVectorLine]))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Polygon layer', type=QgsProcessing.TypeVectorPolygon))

    def processAlgorithm(self, parameters, context, feedback):

        Processing.initialize()
        import processing

        inlayer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        out_Wkb = QgsWkbTypes.Polygon
        
        result = processing.run('qgis:linestopolygons', {'INPUT': inlayer, 'OUTPUT': 'memory:'})

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, inlayer.fields(), out_Wkb, inlayer.sourceCrs())
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        features = result['OUTPUT'].getFeatures()
        total = 100.0 / result['OUTPUT'].featureCount() if result['OUTPUT'].featureCount() else 0
        for current, f in enumerate(features):
            if feedback.isCanceled():
                break
            sink.addFeature(f, QgsFeatureSink.FastInsert)
            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}

    def name(self):
        return 'Tracks to polygons'

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/polygon.png')

    def displayName(self):
        return self.name()

    def group(self):
        return self.groupId()

    def groupId(self):
        return ''

    def createInstance(self):
        return TracksToPolygonsProcessingAlgorithm()
