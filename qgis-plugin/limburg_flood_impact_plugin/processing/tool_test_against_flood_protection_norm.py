from pathlib import Path

from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsVectorFileWriter,
                       QgsProcessingParameterFeatureSource, QgsProcessingFeedback,
                       QgsProcessingContext)

from limburg_flood_impact.test_against_flood_protection_norm import test_against_flood_protection_norm

from .utils import (has_field, reload_layer_in_project)


class TestAgainstFloodProtectionNormAlgorithm(QgsProcessingAlgorithm):

    BUILDINGS_LAYER = "BuildingsLayer"
    FLOOD_LAYER = "FloodLayer"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.BUILDINGS_LAYER, "Buildings Layer",
                                                [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.FLOOD_LAYER, "Flood Protection Norm Layer",
                                                [QgsProcessing.TypeVectorPolygon]))

    def checkParameterValues(self, parameters, context):

        buildings_layer = self.parameterAsVectorLayer(parameters, self.BUILDINGS_LAYER, context)

        flood_layer = self.parameterAsVectorLayer(parameters, self.FLOOD_LAYER, context)

        if 1 < buildings_layer.dataProvider().subLayerCount():
            return False, "Buildings Layer data source has more than one layer."

        if 1 < flood_layer.dataProvider().subLayerCount():
            return False, "Flood Protection Norm Layer data source has more than one layer."

        field_exist, msg = has_field(buildings_layer, "identificatie")

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

        floods_protection_datasource, _ = self.parameterAsCompatibleSourceLayerPathAndLayerName(
            parameters,
            self.FLOOD_LAYER,
            context,
            QgsVectorFileWriter.supportedFormatExtensions(),
            feedback=feedback)

        test_against_flood_protection_norm(Path(buildings_datasource),
                                           Path(floods_protection_datasource),
                                           self.set_feedback_percent,
                                           self.feedback)

        if not self.feedback.isCanceled():
            self.feedback.pushInfo("Column with validation successfully added!")
        else:
            self.feedback.pushWarning("Calculation did not finish, due to user interruption. Only part of the values was calculated.")

        buildings_layer = self.parameterAsVectorLayer(parameters, self.BUILDINGS_LAYER, context)
        reload_layer_in_project(buildings_layer.id())

        return {}

    def set_feedback_percent(self, value: float):
        self.feedback.setProgress(value)

    def name(self):
        return "testagainstfloodprotectionnorm"

    def displayName(self):
        return "Test Against Flood Protection Norm"

    def createInstance(self):
        return TestAgainstFloodProtectionNormAlgorithm()
