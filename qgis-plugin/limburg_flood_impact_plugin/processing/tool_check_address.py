from pathlib import Path

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsVectorFileWriter,
    QgsProcessingParameterFeatureSource,
    QgsProcessingFeedback,
    QgsProcessingContext,
    QgsProcessingParameterString,
)

from limburg_flood_impact.check_address import check_building_have_address
from limburg_flood_impact.default_field_names import DEFAULT_BUILDING_ID_FIELD
from limburg_flood_impact.default_field_names import DEFAULT_ADDRESS_BUILDING_ID_FIELD

from .utils import has_field, reload_layer_in_project


class CheckAddressAlgorithm(QgsProcessingAlgorithm):

    BUILDINGS_LAYER = "BuildingsLayer"
    ADDRESSES_LAYER = "AddressesLayer"
    BUILDING_ID_FIELD = "BUILDING_ID_FIELD"
    ADDRESS_ID_FIELD = "ADDRESS_ID_FIELD"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BUILDINGS_LAYER,
                "Buildings Layer",
                [QgsProcessing.TypeVectorPolygon],
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ADDRESSES_LAYER, "Addresses Layer",
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                name=self.BUILDING_ID_FIELD,
                description="Building ID field",
                defaultValue=DEFAULT_BUILDING_ID_FIELD,
                multiLine=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                name=self.ADDRESS_ID_FIELD,
                description="Address ID field",
                defaultValue=DEFAULT_ADDRESS_BUILDING_ID_FIELD,
                multiLine=False,
            )
        )


    def checkParameterValues(self, parameters, context):

        buildings_layer = self.parameterAsVectorLayer(parameters, self.BUILDINGS_LAYER, context)
        building_id_field = self.parameterAsString(parameters, self.BUILDING_ID_FIELD, context)

        addresses_layer = self.parameterAsVectorLayer(parameters, self.ADDRESSES_LAYER, context)
        address_id_field = self.parameterAsString(parameters, self.ADDRESS_ID_FIELD, context)

        if 1 < buildings_layer.dataProvider().subLayerCount():
            return False, "Buildings Layer data source has more than one layer."

        if 1 < addresses_layer.dataProvider().subLayerCount():
            return False, "Addresses Layer data source has more than one layer."

        field_exist, msg = has_field(addresses_layer, address_id_field)

        if not field_exist:
            return False, msg

        field_exist, msg = has_field(buildings_layer, building_id_field)

        if not field_exist:
            return False, msg

        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):

        buildings_datasource, _ = self.parameterAsCompatibleSourceLayerPathAndLayerName(
            parameters,
            self.BUILDINGS_LAYER,
            context,
            QgsVectorFileWriter.supportedFormatExtensions(),
            feedback=feedback,
        )
        building_id_field = self.parameterAsString(parameters, self.BUILDING_ID_FIELD, context)

        addresses_datasource, _ = self.parameterAsCompatibleSourceLayerPathAndLayerName(
            parameters,
            self.ADDRESSES_LAYER,
            context,
            QgsVectorFileWriter.supportedFormatExtensions(),
            feedback=feedback,
        )
        address_id_field = self.parameterAsString(parameters, self.ADDRESS_ID_FIELD, context)

        check_building_have_address(
            Path(buildings_datasource),
            Path(addresses_datasource),
            building_id_field=building_id_field,
            address_building_id_field=address_id_field,
        )

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
