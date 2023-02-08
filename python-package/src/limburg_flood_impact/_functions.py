from pathlib import Path
import argparse

import numpy as np

from osgeo import ogr, gdal

RASTER_DRIVER: gdal.Driver = gdal.GetDriverByName("MEM")
VECTOR_DRIVER: ogr.Driver = ogr.GetDriverByName("MEMORY")
COLUMN_RASTER_VALUE = "rasterValue"


def convert_to_binary_raster(ds: gdal.Dataset, values_below_as_zero: float = None) -> gdal.Dataset:
    """
    Converts input ds into binary raster (mask). All values besides NoData are converted to 1, NoData is 0.
    If values_below_as_zero parameter is specified, values < values_below_as_zero are also converted to 0.

    Parameters
    ----------
    ds : gdal.Dataset
    values_below_as_zero : float, optional
        by default None

    Returns
    -------
    gdal.Dataset
        Dataset with one band representing the mask.
    """
    dsPath = Path(ds.GetDescription())

    band: gdal.Band = ds.GetRasterBand(1)
    data = band.ReadAsArray()

    binaryData = data.copy()
    binaryData[data == band.GetNoDataValue()] = 0
    if values_below_as_zero:
        binaryData[data < values_below_as_zero] = 0
    binaryData[binaryData != 0] = 1

    rasterName = "br_" + dsPath.stem
    binaryDs = create_empty_raster(rasterName, ds, gdal.GDT_Byte)

    binaryBand: gdal.Band = binaryDs.GetRasterBand(1)
    binaryBand.WriteArray(binaryData.astype(np.byte))

    binaryBand = None
    binaryData = None

    return binaryDs


def create_empty_raster(name: str,
                        template_raster: gdal.Dataset,
                        data_type=gdal.GDT_Byte) -> gdal.Dataset:
    """
    Creates empty raster with single band, with settings copied from template_raster (size, crs, geotransformation) and specified data type.

    Parameters
    ----------
    name : str
    templateRaster : gdal.Dataset
    dataType : _type_, optional
        by default gdal.GDT_Byte

    Returns
    -------
    gdal.Dataset
        Dataset with single band.
    """
    ds: gdal.Dataset = RASTER_DRIVER.Create(name,
                                            template_raster.RasterXSize,
                                            template_raster.RasterYSize,
                                            bands=1,
                                            eType=data_type)
    ds.SetGeoTransform(template_raster.GetGeoTransform())
    ds.SetProjection(template_raster.GetProjection())
    return ds


def create_vector_datasource(fileName: str) -> ogr.DataSource:
    ds: ogr.DataSource = VECTOR_DRIVER.CreateDataSource(fileName)
    return ds


def vectorize_raster(raster_ds: gdal.Dataset,
                     column_name_for_raster_values: str = COLUMN_RASTER_VALUE) -> ogr.DataSource:
    """
    Converts first band of raster_ds into polygon layer with raster values stored in specific column.

    Parameters
    ----------
    raster_ds : gdal.Dataset
    column_name_for_raster_values : str, optional
        by default COLUMN_RASTER_VALUE

    Returns
    -------
    ogr.DataSource
        Datasource with single layer that is vectorization of raster.
    """
    ds_path = Path(raster_ds.GetDescription())

    file_name = "vectorized_" + ds_path.stem

    vector_ds = create_vector_datasource(file_name)

    layer_name = "vectorized_raster_" + ds_path.stem

    layer: ogr.Layer = vector_ds.CreateLayer(layer_name, raster_ds.GetSpatialRef(), ogr.wkbPolygon)

    layer.CreateField(ogr.FieldDefn(column_name_for_raster_values, ogr.OFTReal))

    band: gdal.Band = raster_ds.GetRasterBand(1)
    gdal.Polygonize(band, band.GetMaskBand(), layer, 0)

    band = None

    return vector_ds


def select_features(ds: ogr.DataSource,
                    value_to_select: float,
                    column_to_select_from: str = COLUMN_RASTER_VALUE,
                    min_area: float = None) -> ogr.DataSource:
    """
    Select features from first layer of provided ds based on value from specific column with option to only select features above specific area.

    Parameters
    ----------
    ds : ogr.DataSource
    value_to_select : float
    column_to_select_from : str, optional
        by default COLUMN_RASTER_VALUE
    min_area : float, optional
        by default None

    Returns
    -------
    ogr.DataSource
        DataSource with one layer containing selected features.
    """
    ds_path = Path(ds.GetDescription())

    file_name = "selected" + ds_path.stem

    vector_ds = create_vector_datasource(file_name)

    layer: ogr.Layer = ds.GetLayer()

    geometry_column = layer.GetGeometryColumn()

    if not geometry_column:
        geometry_column = "geometry"

    if min_area:
        sql = f"SELECT * FROM '{layer.GetName()}' WHERE {column_to_select_from} == {value_to_select} AND ST_AREA({geometry_column}) > {min_area}"
    else:
        sql = f"SELECT * FROM '{layer.GetName()}' WHERE {column_to_select_from} == {value_to_select}"

    sql_layer: ogr.Layer = ds.ExecuteSQL(sql, dialect="SQLITE")

    vector_ds.CopyLayer(sql_layer,
                        "selected",
                        options=["DST_SRSWKT=" + layer.GetSpatialRef().ExportToWkt()])

    sql_layer = None

    return vector_ds


def rasterize_layer_mask(ds: ogr.DataSource,
                         template_raster: gdal.Dataset,
                         data_type=gdal.GDT_Float64) -> np.ndarray:
    """
    Converts ds into binary raster mask according to template raster.

    Parameters
    ----------
    ds : ogr.DataSource
    template_raster : gdal.Dataset
    data_type : _type_, optional
        by default gdal.GDT_Float64

    Returns
    -------
    np.ndarray
    """
    layer: ogr.Layer = ds.GetLayer()

    dsPath = Path(ds.GetDescription())

    fileName = "rasterized" + dsPath.stem

    rasterDs = create_empty_raster(fileName, template_raster, data_type)

    gdal.RasterizeLayer(rasterDs, [1], layer, burn_values=[1], options=["ALL_TOUCHED=TRUE"])

    band: gdal.Band = rasterDs.GetRasterBand(1)

    array = band.ReadAsArray()

    rasterDs = None
    band = None

    return array


def multiply_raster_by_mask(raster_ds: gdal.Dataset, mask: np.ndarray) -> gdal.Dataset:
    """
    Creates new raster by multiplying first band of provided raster by the provided mask.

    Parameters
    ----------
    raster_ds : gdal.Dataset
    mask : np.ndarray

    Returns
    -------
    gdal.Dataset
    """
    ds_path = Path(raster_ds.GetDescription())

    file_name = "with_mask" + ds_path.stem

    new_raster_ds = create_empty_raster(file_name, raster_ds, gdal.GDT_Float64)

    band: gdal.Band = new_raster_ds.GetRasterBand(1)

    band.WriteArray(raster_ds.GetRasterBand(1).ReadAsArray() * mask)

    band = None

    return new_raster_ds


def delete_all_features_from_layer(layer: ogr.Layer) -> None:

    fd: ogr.Feature = layer.GetNextFeature()

    while fd:
        layer.DeleteFeature(fd.GetFID())
        fd = layer.GetNextFeature()


def flood_mask(flood_raster_ds: gdal.Dataset,
               only_water_height_above: float = 0.0,
               minimal_area_of_water_pond: float = 0.0) -> gdal.Dataset:
    """
    Handles the steps to create flood Dataset. Can select only pixels with value above specific height and with specified minimal area.
    Returns raster with one band representing the water height only at areas that fullfil requirements.

    Parameters
    ----------
    flood_raster_ds : gdal.Dataset
    only_water_height_above : float, optional
        by default 0.0
    minimal_area_of_water_pond : float, optional
        by default 0.0

    Returns
    -------
    gdal.Dataset
    """

    binary_raster_ds = convert_to_binary_raster(flood_raster_ds,
                                                values_below_as_zero=only_water_height_above)

    vectorized_raster_ds = vectorize_raster(binary_raster_ds)

    selected_areas_ds = select_features(vectorized_raster_ds,
                                        value_to_select=1,
                                        min_area=minimal_area_of_water_pond)

    rasterized_mask = rasterize_layer_mask(selected_areas_ds, flood_raster_ds)

    raster = multiply_raster_by_mask(flood_raster_ds, rasterized_mask)

    return raster


def raster_coordinates(inputX: float,
                       inputY: float,
                       inv_gt,
                       minimal_cell_coordinate: bool = True) -> tuple:
    """
    Convert input coordinate into row and cell of the raster. inv_gt is the inverse geotransform (gdal.InvGeoTransform()) of the raster.

    Parameters
    ----------
    inputX : float
    inputY : float
    inv_gt : _type_
        gdal.InvGeoTransform() of raster.GetGeoTransform()
    minimal_cell_coordinate : bool, optional
        Do we want minimal cell coordinates (generally left upper corner) or maximal coordinates (right lower corner)?
        By default True which means minimal coordinates.

    Returns
    -------
    tuple
        x, y
    """
    x, y = \
        (inv_gt[0] + inv_gt[1] * inputX + inv_gt[2] * inputY), \
        (inv_gt[3] + inv_gt[4] * inputX + inv_gt[5] * inputY)

    if minimal_cell_coordinate:
        x = int(x)
        y = int(y)
    else:
        x = int(round(x + 0.5))
        y = int(round(y + 0.5))

    return (x, y)


def world_coordinates(inputX: float, inputY: float, gt) -> tuple:
    """
    Transforms column and row into world coordinates. gt is raster.GetGeoTransform().

    Parameters
    ----------
    inputX : float
    inputY : float
    gt : _type_
        raster.GetGeoTransform()

    Returns
    -------
    tuple
        x, y
    """
    x, y = \
        (gt[0] + gt[1] * inputX + gt[2] * inputY), \
        (gt[3] + gt[4] * inputX + gt[5] * inputY)
    return x, y


def get_water_height_array(water_band: gdal.Band, minX: float, maxX: float, minY: float,
                           maxY: float) -> np.ndarray:
    """
    Extract small part of the band as an array, with NoDataValues replaced by 0.

    Parameters
    ----------
    water_band : gdal.Band
    minX : float
    maxX : float
    minY : float
    maxY : float

    Returns
    -------
    np.ndarray
    """
    water_array = water_band.ReadAsArray(minX, maxY, int(maxX - minX), int(minY - maxY))
    water_array[water_array == water_band.GetNoDataValue()] = 0
    # cannot be below 0 so filter out
    water_array[water_array < 0] = 0
    # filter out unreasonably large values -> most likely no data not set correctly
    water_array[water_array > 1000] = 0
    return water_array


def common_arguments_parser() -> argparse.ArgumentParser:
    """
    Default arguments for tools buildins and t10, t25, t100.

    Returns
    -------
    argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument(
        '-b',
        '--buildings',
        type=lambda p: Path(p).absolute(),
        help="Path to the file with buildings.",
        required=True
    )

    parser.add_argument(
        '--t10',
        type=lambda p: Path(p).absolute(),
        help="Path to the file with flood depth t10.",
        required=True
    )

    parser.add_argument(
        '--t25',
        type=lambda p: Path(p).absolute(),
        help="Path to the file with flood depth t25.",
        required=True
    )

    parser.add_argument(
        '--t100',
        type=lambda p: Path(p).absolute(),
        help="Path to the file with flood depth t100.",
        required=True
    )

    return parser


def print_percent(value: float) -> None:
    """
    Function used as callback to print the currently done percent of features.

    Parameters
    ----------
    value : float
        Percent.
    """
    print(f"Done: {round(value, 2)}%.", end="\r")


def find_or_create_field(layer: ogr.Layer,
                         field_name: str,
                         field_type=ogr.OFTReal) -> int:
    """
    Find out if field exist in layer and if not, create it with specified field type.

    Parameters
    ----------
    layer : ogr.Layer
        Layer to search.
    field_name : str
        Field name to look for.
    field_type : Any
        Type of field to create if it does not exist.

    Returns
    -------
    int
        specifies index of the field either before or after creation.
    """

    index = layer.FindFieldIndex(field_name, True)

    if index == -1:
        layer.CreateField(ogr.FieldDefn(field_name, field_type))
        index = layer.FindFieldIndex(field_name, True)

    return index
