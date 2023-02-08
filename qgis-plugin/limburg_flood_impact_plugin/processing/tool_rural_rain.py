from pathlib import Path

from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsVectorFileWriter,
                       QgsProcessingParameterFeatureSource, QgsProcessingFeedback,
                       QgsProcessingContext, QgsProcessingParameterRasterLayer)

from limburg_flood_impact.classify_rural_rain import classify_rural_rain

from .utils import (reload_layer_in_project, get_raster_path, has_one_band, has_field)


class ClassifyRuralRainAlgorithm(QgsProcessingAlgorithm):

    BUILDINGS_LAYER = "BuildingsLayer"
    T10_LAYER = "T10Layer"
    T25_LAYER = "T25Layer"
    T100_LAYER = "T100Layer"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.BUILDINGS_LAYER, "Buildings Layer",
                                                [QgsProcessing.SourceType.TypeVectorPolygon]))

        self.addParameter(QgsProcessingParameterRasterLayer(self.T10_LAYER, "T10"))

        self.addParameter(QgsProcessingParameterRasterLayer(self.T25_LAYER, "T25"))

        self.addParameter(QgsProcessingParameterRasterLayer(self.T100_LAYER, "T100"))

    def checkParameterValues(self, parameters, context):

        t10_raster = self.parameterAsRasterLayer(parameters, self.T10_LAYER, context)
        t25_raster = self.parameterAsRasterLayer(parameters, self.T25_LAYER, context)
        t100_raster = self.parameterAsRasterLayer(parameters, self.T100_LAYER, context)

        single_band, msg = has_one_band(t10_raster)

        if not single_band:
            return False, msg

        single_band, msg = has_one_band(t25_raster)

        if not single_band:
            return False, msg

        single_band, msg = has_one_band(t100_raster)

        if not single_band:
            return False, msg

        buildings = self.parameterAsLayer(parameters, self.BUILDINGS_LAYER, context)

        field_exist, msg = has_field(buildings, "identificatie")

        if not field_exist:
            return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context: QgsProcessingContext,
                         feedback: QgsProcessingFeedback):

        self.feedback = feedback

        buildings_datasource, _ = self.parameterAsCompatibleSourceLayerPathAndLayerName(
            parameters,
            self.BUILDINGS_LAYER,
            context,
            QgsVectorFileWriter.supportedFormatExtensions(),
            feedback=feedback)

        t10_raster = self.parameterAsRasterLayer(parameters, self.T10_LAYER, context)
        t25_raster = self.parameterAsRasterLayer(parameters, self.T25_LAYER, context)
        t100_raster = self.parameterAsRasterLayer(parameters, self.T100_LAYER, context)

        t10_path = get_raster_path(t10_raster)
        t25_path = get_raster_path(t25_raster)
        t100_path = get_raster_path(t100_raster)

        classify_rural_rain(Path(buildings_datasource), t10_path, t25_path, t100_path,
                            self.set_feedback_percent, self.feedback)

        if not self.feedback.isCanceled():
            self.feedback.pushInfo("Column with classification successfully added!")
        else:
            self.feedback.pushWarning("Calculation did not finish, due to user interruption. Only part of the values was calculated.")

        buildings_layer = self.parameterAsVectorLayer(parameters, self.BUILDINGS_LAYER, context)
        reload_layer_in_project(buildings_layer.id())

        return {}

    def set_feedback_percent(self, value: float):
        self.feedback.setProgress(value)

    def name(self):
        return "classifyruralrain"

    def displayName(self):
        return "Classify Rural Rain"

    def createInstance(self):
        return ClassifyRuralRainAlgorithm()
