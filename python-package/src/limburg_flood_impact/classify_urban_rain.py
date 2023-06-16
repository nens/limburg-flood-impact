from pathlib import Path
from typing import Callable

import numpy as np
from osgeo import gdal, ogr

from ._functions import (
    RASTER_DRIVER,
    VECTOR_DRIVER,
    delete_all_features_from_layer,
    find_or_create_field,
    flood_mask,
    get_extent,
    get_water_height_array,
    raster_coordinates,
    world_coordinates,
)


def classify_water_height(
    buildings_layer: ogr.Layer,
    t10: gdal.Dataset,
    t25: gdal.Dataset,
    t100: gdal.Dataset,
    field_name: str = "stedelijk",
    callback_function: Callable[[float], None] = None,
    qgis_feedback=None,
):
    t10_index = find_or_create_field(buildings_layer, f"{field_name}_t10", ogr.OFTString)
    t25_index = find_or_create_field(buildings_layer, f"{field_name}_t25", ogr.OFTString)
    t100_index = find_or_create_field(buildings_layer, f"{field_name}_t100", ogr.OFTString)

    water_depth_t10_index = find_or_create_field(buildings_layer, f"max_waterdiepte_{field_name}_t10", ogr.OFTReal)
    water_depth_t25_index = find_or_create_field(buildings_layer, f"max_waterdiepte_{field_name}_t25", ogr.OFTReal)
    water_depth_t100_index = find_or_create_field(buildings_layer, f"max_waterdiepte_{field_name}_t100", ogr.OFTReal)

    inv_gt = gdal.InvGeoTransform(t10.GetGeoTransform())
    gt = t10.GetGeoTransform()

    t10_band: gdal.Band = t10.GetRasterBand(1)
    t25_band: gdal.Band = t25.GetRasterBand(1)
    t100_band: gdal.Band = t100.GetRasterBand(1)

    memory_ds: ogr.DataSource = VECTOR_DRIVER.CreateDataSource("ds")
    memory_layer: ogr.Layer = memory_ds.CreateLayer("geometry_layer", buildings_layer.GetSpatialRef(), ogr.wkbPolygon)

    raster_bbox = get_extent(t10)

    feature: ogr.Feature
    i = 0
    for feature in buildings_layer:
        if qgis_feedback is not None:
            if qgis_feedback.isCanceled():
                break

        delete_all_features_from_layer(memory_layer)

        geom: ogr.Geometry = feature.GetGeometryRef().Buffer(1)

        if not raster_bbox.Intersect(geom):
            continue

        if not geom.Within(raster_bbox):
            geom = geom.Intersection(raster_bbox)

        minX, maxX, minY, maxY = geom.GetEnvelope()

        new_feature: ogr.Feature = ogr.Feature(memory_layer.GetLayerDefn())
        new_feature.SetGeometry(geom)
        memory_layer.SetFeature(new_feature)

        rMinX, rMaxY = raster_coordinates(minX, maxY, inv_gt)
        rMaxX, rMinY = raster_coordinates(maxX, minY, inv_gt, False)

        feature_raster_ds: gdal.Dataset = RASTER_DRIVER.Create(
            "geom_raster",
            int(rMaxX - rMinX),
            int(rMinY - rMaxY),
            bands=1,
            eType=gdal.GDT_Float64,
        )
        t_coords = world_coordinates(rMinX, rMaxY, gt)
        feature_raster_ds.SetGeoTransform([t_coords[0], gt[1], gt[2], t_coords[1], gt[4], gt[5]])
        feature_raster_ds.SetProjection(t10.GetProjection())

        gdal.RasterizeLayer(
            feature_raster_ds,
            [1],
            memory_layer,
            burn_values=[1],
            options=["ALL_TOUCHED=TRUE"],
        )

        feature_rasterized = feature_raster_ds.GetRasterBand(1).ReadAsArray()

        t10_water = get_water_height_array(t10_band, rMinX, rMaxX, rMinY, rMaxY)
        t25_water = get_water_height_array(t25_band, rMinX, rMaxX, rMinY, rMaxY)
        t100_water = get_water_height_array(t100_band, rMinX, rMaxX, rMinY, rMaxY)

        t10_max_water_height = np.max(feature_rasterized * t10_water)
        t25_max_water_height = np.max(feature_rasterized * t25_water)
        t100_max_water_height = np.max(feature_rasterized * t100_water)

        feature.SetField(water_depth_t10_index, float(t10_max_water_height))
        feature.SetField(water_depth_t25_index, float(t25_max_water_height))
        feature.SetField(water_depth_t100_index, float(t100_max_water_height))

        feature.SetField(t10_index, column_value(t10_max_water_height))
        feature.SetField(t25_index, column_value(t25_max_water_height))
        feature.SetField(t100_index, column_value(t100_max_water_height))

        buildings_layer.SetFeature(feature)

        if callback_function:
            callback_function((i / buildings_layer.GetFeatureCount()) * 100)

        i += 1

    memory_layer = None
    memory_ds = None


def column_value(value: float) -> str:
    if 0.15 < value:
        return "Risico"
    else:
        return "Geen risico"


def classify_urban_rain(
    buildings_path: Path,
    t10: Path,
    t25: Path,
    t100: Path,
    callback_function: Callable[[float], None] = None,
    qgis_feedback=None,
):
    gdal.UseExceptions()

    buildings_ds: ogr.DataSource = ogr.Open(buildings_path.as_posix(), True)
    buildings_layer: ogr.Layer = buildings_ds.GetLayer()

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

    classify_water_height(
        buildings_layer,
        t10_masked,
        t25_masked,
        t100_masked,
        field_name="stedelijk",
        callback_function=callback_function,
        qgis_feedback=qgis_feedback,
    )

    buildings_layer = None
    buildings_ds = None
    t10_ds = None
    t25_ds = None
    t100_ds = None
    t10_masked = None
    t25_masked = None
    t100_masked = None
