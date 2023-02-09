from pathlib import Path
from typing import Callable

from osgeo import ogr

from ._functions import (find_or_create_field)

VOLDOET_AAN_NORM_CLASSES = {
    "Geen risico": "Ja",
    "Lokaal": "Ja",
    "Gecombineerd": "Nader onderzoeken",
    "Landelijk": "Nader onderzoeken",
    "Stedelijk": "Ja",
    "Landelijk en stedelijk": "Nader onderzoeken"
}


def test_against_flood_protection_norm(buildings_path: Path,
                                       flood_norm_path: Path,
                                       callback_function: Callable[[float], None] = None,
                                       qgis_feedback=None):

    buildings_ds: ogr.DataSource = ogr.Open(buildings_path.as_posix(), True)
    flood_norm_ds: ogr.DataSource = ogr.Open(flood_norm_path.as_posix(), True)

    buildings_layer: ogr.Layer = buildings_ds.GetLayer()
    flood_norm_layer: ogr.Layer = flood_norm_ds.GetLayer()

    normgebied_t10_index = find_or_create_field(buildings_layer, "in_normgebied_t10", ogr.OFSTBoolean)
    normgebied_t25_index = find_or_create_field(buildings_layer, "in_normgebied_t25", ogr.OFSTBoolean)
    normgebied_t100_index = find_or_create_field(buildings_layer, "in_normgebied_t100", ogr.OFSTBoolean)
    normgebied_index = find_or_create_field(buildings_layer, "normgebied", ogr.OFTString)
    toetsingsklasse_index = find_or_create_field(buildings_layer, "toetsingsklasse", ogr.OFTString)
    voldoet_aan_norm_index = find_or_create_field(buildings_layer, "voldoet_aan_norm", ogr.OFTString)

    building_feature: ogr.Feature
    i = 0
    for building_feature in buildings_layer:

        if qgis_feedback is not None:
            if qgis_feedback.isCanceled():
                break

        building_geometry: ogr.Geometry = building_feature.geometry()

        flood_norm_layer.SetSpatialFilter(building_geometry)

        flood_feature: ogr.Feature
        for flood_feature in flood_norm_layer:

            flood_geometry: ogr.Geometry = flood_feature.geometry()

            flood_norm = flood_feature.GetFieldAsString("NORM")

            if building_geometry.Intersect(flood_geometry):

                if flood_norm == "1:10":
                    building_feature.SetField(normgebied_t10_index, "True")
                    building_feature.SetField(normgebied_t25_index, "False")
                    building_feature.SetField(normgebied_t100_index, "False")
                    building_feature.SetField(toetsingsklasse_index, building_feature.GetFieldAsString("klasse_t10"))
                elif flood_norm == "1:25":
                    building_feature.SetField(normgebied_t10_index, "False")
                    building_feature.SetField(normgebied_t25_index, "True")
                    building_feature.SetField(normgebied_t100_index, "False")
                    building_feature.SetField(toetsingsklasse_index, building_feature.GetFieldAsString("klasse_t25"))
                elif flood_norm == "1:100":
                    building_feature.SetField(normgebied_t10_index, "False")
                    building_feature.SetField(normgebied_t25_index, "False")
                    building_feature.SetField(normgebied_t100_index, "True")
                    building_feature.SetField(toetsingsklasse_index, building_feature.GetFieldAsString("klasse_t100"))
                else:
                    building_feature.SetField(normgebied_t10_index, "False")
                    building_feature.SetField(normgebied_t25_index, "False")
                    building_feature.SetField(normgebied_t100_index, "False")
                    building_feature.SetField(toetsingsklasse_index, "n.v.t.")

        building_feature.SetField(normgebied_index, flood_norm)
        building_feature.SetField(voldoet_aan_norm_index,
                                  VOLDOET_AAN_NORM_CLASSES[building_feature.GetFieldAsString("toetsingsklasse")])

        buildings_layer.SetFeature(building_feature)

        if callback_function:
            callback_function((i / buildings_layer.GetFeatureCount()) * 100)

        i += 1

    buildings_layer = None
    flood_norm_layer = None
    buildings_ds = None
    flood_norm_ds = None
