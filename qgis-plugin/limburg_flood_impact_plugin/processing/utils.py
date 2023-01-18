from pathlib import Path
from typing import Tuple

from qgis.core import (QgsVectorLayer, QgsProject, QgsProviderRegistry, QgsRasterLayer)


def get_datasource_path(layer: QgsVectorLayer) -> Path:

    uri = layer.dataProvider().uri().uri()

    path = uri.split("|")[0].strip()
    path = Path(path)

    return path


def get_raster_path(layer: QgsRasterLayer) -> Path:

    path = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(),
                                                    layer.source())['path']

    return Path(path)


def has_field(layer: QgsVectorLayer, field_name: str) -> Tuple[bool, str]:

    fields = layer.fields()

    if field_name in fields.names():
        return True, ""

    return False, f"{layer.name()} does not have a field `{field_name}` which is required."


def has_one_band(layer: QgsRasterLayer) -> Tuple[bool, str]:

    if layer.bandCount() == 1:
        return True, ""

    return False, f"{layer.name()} has more then one band. Raster layer needs to have only single band."


def reload_layer_in_project(layer_id: str) -> None:
    layer = QgsProject.instance().mapLayer(layer_id)
    layer.reload()
