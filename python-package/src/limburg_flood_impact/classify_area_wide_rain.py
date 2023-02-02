from typing import Callable
from pathlib import Path

import numpy as np

from osgeo import ogr, gdal

from ._functions import RASTER_DRIVER, VECTOR_DRIVER
from ._functions import (flood_mask, delete_all_features_from_layer, raster_coordinates,
                         world_coordinates, get_water_height_array)


def classify_water_height(buildings_ds: gdal.Dataset,
                          t10_with_puddles: gdal.Dataset,
                          t25_with_puddles: gdal.Dataset,
                          t100_with_puddles: gdal.Dataset,
                          t10: gdal.Dataset,
                          t25: gdal.Dataset,
                          t100: gdal.Dataset,
                          field_name: str = "gebiedsbreed",
                          callback_function: Callable[[float], None] = None,
                          qgis_feedback=None):

    buildings_layer: ogr.Layer = buildings_ds.GetLayer()

    t10_index = buildings_layer.FindFieldIndex(f"{field_name}_t10", True)
    t25_index = buildings_layer.FindFieldIndex(f"{field_name}_t25", True)
    t100_index = buildings_layer.FindFieldIndex(f"{field_name}_t100", True)

    if t10_index == -1:
        buildings_layer.CreateField(ogr.FieldDefn(f"{field_name}_t10", ogr.OFTString))
        t10_index = buildings_layer.FindFieldIndex(f"{field_name}_t10", True)

    if t25_index == -1:
        buildings_layer.CreateField(ogr.FieldDefn(f"{field_name}_t25", ogr.OFTString))
        t25_index = buildings_layer.FindFieldIndex(f"{field_name}_t25", True)

    if t100_index == -1:
        buildings_layer.CreateField(ogr.FieldDefn(f"{field_name}_t100", ogr.OFTString))
        t100_index = buildings_layer.FindFieldIndex(f"{field_name}_t100", True)

    inv_gt = gdal.InvGeoTransform(t10.GetGeoTransform())
    gt = t10.GetGeoTransform()

    t10_band_with_puddles: gdal.Band = t10_with_puddles.GetRasterBand(1)
    t25_band_with_puddles: gdal.Band = t25_with_puddles.GetRasterBand(1)
    t100_band_with_puddles: gdal.Band = t100_with_puddles.GetRasterBand(1)

    t10_band: gdal.Band = t10.GetRasterBand(1)
    t25_band: gdal.Band = t25.GetRasterBand(1)
    t100_band: gdal.Band = t100.GetRasterBand(1)

    memory_ds: ogr.DataSource = VECTOR_DRIVER.CreateDataSource("ds")
    memory_layer: ogr.Layer = memory_ds.CreateLayer("geometry_layer",
                                                    buildings_layer.GetSpatialRef(),
                                                    ogr.wkbPolygon)

    feature: ogr.Feature
    i = 0
    for feature in buildings_layer:

        if qgis_feedback is not None:
            if qgis_feedback.isCanceled():
                break

        delete_all_features_from_layer(memory_layer)

        geom: ogr.Geometry = feature.GetGeometryRef().Buffer(1)
        minX, maxX, minY, maxY = geom.GetEnvelope()

        new_feature: ogr.Feature = ogr.Feature(memory_layer.GetLayerDefn())
        new_feature.SetGeometry(geom)
        memory_layer.SetFeature(new_feature)

        rMinX, rMaxY = raster_coordinates(minX, maxY, inv_gt)
        rMaxX, rMinY = raster_coordinates(maxX, minY, inv_gt, False)

        feature_raster_ds: gdal.Dataset = RASTER_DRIVER.Create("geom_raster",
                                                               int(rMaxX - rMinX),
                                                               int(rMinY - rMaxY),
                                                               bands=1,
                                                               eType=gdal.GDT_Float64)
        t_coords = world_coordinates(rMinX, rMaxY, gt)
        feature_raster_ds.SetGeoTransform([t_coords[0], gt[1], gt[2], t_coords[1], gt[4], gt[5]])
        feature_raster_ds.SetProjection(t10.GetProjection())

        gdal.RasterizeLayer(feature_raster_ds, [1],
                            memory_layer,
                            burn_values=[1],
                            options=["ALL_TOUCHED=TRUE"])

        feature_rasterized = feature_raster_ds.GetRasterBand(1).ReadAsArray()

        t10_water_with_puddles = get_water_height_array(t10_band_with_puddles, rMinX, rMaxX, rMinY,
                                                        rMaxY)
        t25_water_with_puddles = get_water_height_array(t25_band_with_puddles, rMinX, rMaxX, rMinY,
                                                        rMaxY)
        t100_water_with_puddles = get_water_height_array(t100_band_with_puddles, rMinX, rMaxX,
                                                         rMinY, rMaxY)

        t10_water = get_water_height_array(t10_band, rMinX, rMaxX, rMinY, rMaxY)
        t25_water = get_water_height_array(t25_band, rMinX, rMaxX, rMinY, rMaxY)
        t100_water = get_water_height_array(t100_band, rMinX, rMaxX, rMinY, rMaxY)

        feature.SetField(
            t10_index,
            column_value(np.max(feature_rasterized * t10_water_with_puddles),
                         np.max(feature_rasterized * t10_water)))
        feature.SetField(
            t25_index,
            column_value(np.max(feature_rasterized * t25_water_with_puddles),
                         np.max(feature_rasterized * t25_water)))
        feature.SetField(
            t100_index,
            column_value(np.max(feature_rasterized * t100_water_with_puddles),
                         np.max(feature_rasterized * t100_water)))

        buildings_layer.SetFeature(feature)

        if callback_function:
            callback_function((i / buildings_layer.GetFeatureCount()) * 100)

        i += 1

    buildings_layer = None


def column_value(value_with_puddles: float, value_without_puddles: float) -> str:
    if 0.15 < value_with_puddles and value_without_puddles <= 0.15:
        return "Risico, lokale herkomst"
    elif 0.15 < value_without_puddles:
        return "Risico, regionale herkomst"
    elif value_with_puddles <= 0.15:
        return "Geen risico"

    return "Geen risico"


def classify_area_wide_rain(buildings_path: Path,
                            t10: Path,
                            t25: Path,
                            t100: Path,
                            callback_function: Callable[[float], None] = None,
                            qgis_feedback=None):

    buildings_ds: ogr.DataSource = ogr.Open(buildings_path.as_posix(), True)

    t10_ds: gdal.Dataset = gdal.Open(t10.as_posix())
    t25_ds: gdal.Dataset = gdal.Open(t25.as_posix())
    t100_ds: gdal.Dataset = gdal.Open(t100.as_posix())

    t10_masked_including_puddles = flood_mask(t10_ds, only_water_height_above=0.02)

    if qgis_feedback:
        if qgis_feedback.isCanceled():
            return

    t25_masked_including_puddles = flood_mask(t25_ds, only_water_height_above=0.02)

    if qgis_feedback:
        if qgis_feedback.isCanceled():
            return

    t100_masked_including_puddles = flood_mask(t100_ds, only_water_height_above=0.02)

    if qgis_feedback:
        if qgis_feedback.isCanceled():
            return

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
                          t10_masked_including_puddles,
                          t25_masked_including_puddles,
                          t100_masked_including_puddles,
                          t10_masked,
                          t25_masked,
                          t100_masked,
                          callback_function=callback_function,
                          qgis_feedback=qgis_feedback)

    buildings_ds = None
    t10_ds = None
    t25_ds = None
    t100_ds = None
