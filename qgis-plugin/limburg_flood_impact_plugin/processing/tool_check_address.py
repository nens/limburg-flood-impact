from pathlib import Path

from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsVectorFileWriter,
                       QgsProcessingParameterFeatureSource, QgsProcessingFeedback,
                       QgsProcessingContext)

from limburg_flood_impact.check_address import check_building_have_address

from .utils import (has_field, reload_layer_in_project)


class CheckAddressAlgorithm(QgsProcessingAlgorithm):

    BUILDINGS_LAYER = "BuildingsLayer"
    ADDRESSES_LAYER = "AddressesLayer"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.BUILDINGS_LAYER, "Buildings Layer",
                                                [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.ADDRESSES_LAYER, "Addresses Layer",
                                                [QgsProcessing.TypeVectorPoint]))

    def checkParameterValues(self, parameters, context):

        buildings_layer = self.parameterAsVectorLayer(parameters, self.BUILDINGS_LAYER, context)

        addresses_layer = self.parameterAsVectorLayer(parameters, self.ADDRESSES_LAYER, context)

        if 1 < buildings_layer.dataProvider().subLayerCount():
            return False, "Buildings Layer data source has more than one layer."

        if 1 < addresses_layer.dataProvider().subLayerCount():
            return False, "Addresses Layer data source has more than one layer."

        field_exist, msg = has_field(addresses_layer, "pandidentificatie")

        if not field_exist:
            return False, msg

        field_exist, msg = has_field(buildings_layer, "identificatie")

        if not field_exist:
            return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context: QgsProcessingContext,
                         feedback: QgsProcessingFeedback):

        buildings_datasource, _ = self.parameterAsCompatibleSourceLayerPathAndLayerName(
            parameters,
            self.BUILDINGS_LAYER,
            context,
            QgsVectorFileWriter.supportedFormatExtensions(),
            feedback=feedback)

        addresses_datasource, _ = self.parameterAsCompatibleSourceLayerPathAndLayerName(
            parameters,
            self.ADDRESSES_LAYER,
            context,
            QgsVectorFileWriter.supportedFormatExtensions(),
            feedback=feedback)

        check_building_have_address(Path(buildings_datasource), Path(addresses_datasource))

        feedback.pushInfo("heeft_adres column successfully added!")

        buildings_layer = self.parameterAsVectorLayer(parameters, self.BUILDINGS_LAYER, context)
        reload_layer_in_project(buildings_layer.id())

        return {}

    def name(self):
        return "checkaddresses"

    def displayName(self):
        return "Check Addresses"

    def createInstance(self):
        return CheckAddressAlgorithm()
