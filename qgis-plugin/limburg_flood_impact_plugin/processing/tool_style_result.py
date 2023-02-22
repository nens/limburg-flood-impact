from pathlib import Path

from qgis.core import (QgsProcessing, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource, QgsProcessingFeedback,
                       QgsProcessingContext, QgsProcessingParameterEnum, QgsCategorizedSymbolRenderer)

from .utils import (has_field, reload_layer_in_project)


class StyleResultAlgorithm(QgsProcessingAlgorithm):

    BUILDINGS_LAYER = "BuildingsLayer"
    FIELD = "Field"

    fields = ["landelijk_t10", "landelijk_t25", "landelijk_t100",
              "stedelijk_10", "stedelijk_t25", "stedelijk_t100",
              "gebiedsbreed_10", "gebiedsbreed_t25", "gebiedsbreed_t100",
              "klasse_t10", "klasse_25", "klasse_25"]

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.BUILDINGS_LAYER, "Buildings Layer",
                                                [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(
            QgsProcessingParameterEnum(self.FIELD, "Select Field to Style", self.fields, False))

    def checkParameterValues(self, parameters, context):

        buildings_layer = self.parameterAsVectorLayer(parameters, self.BUILDINGS_LAYER, context)

        if 1 < buildings_layer.dataProvider().subLayerCount():
            return False, "Buildings Layer data source has more than one layer."

        field_exist, msg = has_field(buildings_layer, "identificatie")

        if not field_exist:
            return False, msg

        field_number = self.parameterAsEnum(parameters, self.FIELD, context)

        field_name = self.fields[field_number]

        if field_name not in buildings_layer.fields().names():
            return False, f"Selected field `{field_name}` does not exit in the layer. Cannot continue."

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context: QgsProcessingContext,
                         feedback: QgsProcessingFeedback):

        buildings_layer = self.parameterAsVectorLayer(parameters, self.BUILDINGS_LAYER, context)
        field_number = self.parameterAsEnum(parameters, self.FIELD, context)

        field_to_style = self.fields[field_number]

        file_name = "klasse.qml"

        if field_to_style in ["landelijk_t10", "landelijk_t25", "landelijk_t100", "stedelijk_10", "stedelijk_t25", "stedelijk_t100"]:
            file_name = "landelijk_stedelijk.qml"
        elif field_to_style in ["gebiedsbreed_10", "gebiedsbreed_t25", "gebiedsbreed_t100"]:
            file_name = "gebiedsbreed.qml"
        elif field_to_style in ["klasse_t10", "klasse_25", "klasse_100"]:
            file_name = "klasse.qml"

        qml_file = Path(__file__).parent.parent / "style" / file_name

        buildings_layer.loadNamedStyle(qml_file.as_posix())

        renderer: QgsCategorizedSymbolRenderer = buildings_layer.renderer()

        renderer.setClassAttribute(field_to_style)

        reload_layer_in_project(buildings_layer.id())

        return {}

    def name(self):
        return "styleresultfield"

    def displayName(self):
        return "Style Layer using Field"

    def createInstance(self):
        return StyleResultAlgorithm()
