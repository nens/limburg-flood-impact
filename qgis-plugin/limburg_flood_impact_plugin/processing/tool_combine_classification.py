from pathlib import Path

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsVectorFileWriter,
    QgsProcessingParameterFeatureSource,
    QgsProcessingFeedback,
    QgsProcessingContext,
)

from limburg_flood_impact.combine_classification import (
    combine_classification,
    REQUIRED_COLUMNS,
)

from .utils import has_field, reload_layer_in_project


class CombineClassificationAlgorithm(QgsProcessingAlgorithm):

    BUILDINGS_LAYER = "BuildingsLayer"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BUILDINGS_LAYER,
                "Buildings Layer",
                [QgsProcessing.TypeVectorPolygon],
            )
        )

    def checkParameterValues(self, parameters, context):

        buildings_layer = self.parameterAsVectorLayer(parameters, self.BUILDINGS_LAYER, context)

        if 1 < buildings_layer.dataProvider().subLayerCount():
            return False, "Buildings Layer data source has more than one layer."

        for column in REQUIRED_COLUMNS:

            field_exist, msg = has_field(buildings_layer, column)

            if not field_exist:
                return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):

        self.feedback = feedback

        buildings_datasource, _ = self.parameterAsCompatibleSourceLayerPathAndLayerName(
            parameters,
            self.BUILDINGS_LAYER,
            context,
            QgsVectorFileWriter.supportedFormatExtensions(),
            feedback=feedback,
        )

        combine_classification(Path(buildings_datasource), self.set_feedback_percent)

        feedback.pushInfo("Combined classification column successfully added!")

        buildings_layer = self.parameterAsVectorLayer(parameters, self.BUILDINGS_LAYER, context)
        reload_layer_in_project(buildings_layer.id())

        return {}

    def name(self):
        return "combineclassification"

    def displayName(self):
        return "Combine Classification"

    def createInstance(self):
        return CombineClassificationAlgorithm()

    def set_feedback_percent(self, value: float):
        self.feedback.setProgress(value)
