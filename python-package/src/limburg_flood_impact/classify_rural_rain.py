from typing import Callable
from pathlib import Path

from osgeo import ogr, gdal

from ._functions import (flood_mask)
from .classify_urban_rain import classify_water_height


def classify_rural_rain(buildings_path: Path,
                        t10: Path,
                        t25: Path,
                        t100: Path,
                        callback_function: Callable[[float], None] = None,
                        qgis_feedback=None):

    buildings_ds: ogr.DataSource = ogr.Open(buildings_path.as_posix(), True)

    t10_ds: gdal.Dataset = gdal.Open(t10.as_posix())
    t25_ds: gdal.Dataset = gdal.Open(t25.as_posix())
    t100_ds: gdal.Dataset = gdal.Open(t100.as_posix())

    t10_masked = flood_mask(t10_ds, only_water_height_above=0.02, minimal_area_of_water_pond=200)

    if qgis_feedback:
        if qgis_feedback.isCanceled():
            return

    t25_masked = flood_mask(t25_ds, only_water_height_above=0.02, minimal_area_of_water_pond=200)

    if qgis_feedback:
        if qgis_feedback.isCanceled():
            return

    t100_masked = flood_mask(t100_ds, only_water_height_above=0.02, minimal_area_of_water_pond=200)

    if qgis_feedback:
        if qgis_feedback.isCanceled():
            return

    classify_water_height(buildings_ds,
                          t10_masked,
                          t25_masked,
                          t100_masked,
                          field_name="landelijk",
                          callback_function=callback_function,
                          qgis_feedback=qgis_feedback)

    buildings_ds = None
    t10_ds = None
    t25_ds = None
    t100_ds = None
