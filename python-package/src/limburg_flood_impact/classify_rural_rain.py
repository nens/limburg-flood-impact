from pathlib import Path
import gc
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
    tmp_building_layer: ogr.Layer = buildings_ds.GetLayer()

    driver_mem: ogr.Driver = ogr.GetDriverByName("MEMORY")
    source_mem: ogr.DataSource = driver_mem.CreateDataSource("memData")
    buildings_layer: ogr.Layer = source_mem.CopyLayer(
        tmp_building_layer, tmp_building_layer.GetName(), ["OVERWRITE=YES"]
    )

    del tmp_building_layer

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

        if qgis_feedback and qgis_feedback.isCanceled():
            # Clean up and return if feedback is canceled
            del t10_ds, t25_ds, t100_ds, t10_masked
            gc.collect()
            return

        t25_masked = flood_mask(t25_ds, only_water_height_above=0.02, minimal_area_of_water_pond=200)

        if qgis_feedback and qgis_feedback.isCanceled():
            # Clean up and return if feedback is canceled
            del t10_ds, t25_ds, t100_ds, t10_masked, t25_masked
            gc.collect()
            return

        t100_masked = flood_mask(t100_ds, only_water_height_above=0.02, minimal_area_of_water_pond=200)

        if qgis_feedback and qgis_feedback.isCanceled():
            # Clean up and return if feedback is canceled
            del t10_ds, t25_ds, t100_ds, t10_masked, t25_masked, t100_masked
            gc.collect()
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

        # Clean up
        del t10_ds, t25_ds, t100_ds, t10_masked, t25_masked, t100_masked
        gc.collect()

    buildings_ds.CopyLayer(buildings_layer, buildings_layer.GetName(), ["OVERWRITE=YES"])

    # Final clean up
    del buildings_layer, buildings_ds, t10_ds_whole, t25_ds_whole, t100_ds_whole, driver_mem, source_mem, tiles, rasterExtent
    gc.collect()

if __name__ == "__main__":
    classify_rural_rain(
        Path("/home/cahik/Lutra/Floods/New_Data/Overig benodigde data/BAG_panden.gpkg"),
        Path("/home/cahik/Lutra/Floods/New_Data/rasters/T10Compleet.tif"),
        Path("/home/cahik/Lutra/Floods/New_Data/rasters/T25Compleet.tif"),
        Path("/home/cahik/Lutra/Floods/New_Data/rasters/T100Compleet.tif"),
    )
