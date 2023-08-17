from pathlib import Path

from osgeo import gdal, ogr

from ._functions import TILE_OVERLAP, TILE_SIZE, flood_mask, print_progress_bar
from .classify_urban_rain import classify_water_height
from .extent_tile import Extent


def classify_rural_rain(
    buildings_path: Path,
    t10: Path,
    t25: Path,
    t100: Path,
    qgis_feedback=None,
):
    gdal.UseExceptions()

    buildings_ds: ogr.DataSource = ogr.Open(buildings_path.as_posix(), True)
    buildings_layer: ogr.Layer = buildings_ds.GetLayer()

    t10_ds_whole: gdal.Dataset = gdal.Open(t10.as_posix())
    t25_ds_whole: gdal.Dataset = gdal.Open(t25.as_posix())
    t100_ds_whole: gdal.Dataset = gdal.Open(t100.as_posix())

    rasterExtent = Extent.from_gdal_ds(t10_ds_whole)

    tiles = rasterExtent.create_tiles(TILE_SIZE)

    for i, tile in enumerate(tiles):
        buildings_layer.ResetReading()

        if qgis_feedback is None:
            print_progress_bar(i + 1, len(tiles), "Tiles processed.")

        tile.buffer_by(TILE_OVERLAP)

        t10_ds = tile.extract_from(t10_ds_whole)
        t25_ds = tile.extract_from(t25_ds_whole)
        t100_ds = tile.extract_from(t100_ds_whole)

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
            field_name="landelijk",
            qgis_feedback=qgis_feedback,
        )

        if qgis_feedback:
            qgis_feedback.setProgress(((i + 1) / len(tiles)) * 100)

    buildings_layer = None
    buildings_ds = None
    t10_ds = None
    t25_ds = None
    t100_ds = None
    t10_masked = None
    t25_masked = None
    t100 = None
