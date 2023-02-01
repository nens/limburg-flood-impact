from pathlib import Path

from osgeo import ogr


def check_building_have_address(buildings_path: Path, adresses_path: Path):

    buildings_ds: ogr.DataSource = ogr.Open(buildings_path.as_posix(), True)
    buildings_layer: ogr.Layer = buildings_ds.GetLayer()

    adresses_ds: ogr.DataSource = ogr.Open(adresses_path.as_posix())
    adresses_layer: ogr.Layer = adresses_ds.GetLayer()

    memory_driver: ogr.Driver = ogr.GetDriverByName("MEMORY")

    memory_ds: ogr.DataSource = memory_driver.CreateDataSource("ds")
    memory_ds.CopyLayer(buildings_layer, "buildings")
    memory_ds.CopyLayer(adresses_layer, "adresses")

    buildings_layer_copied: ogr.Layer = memory_ds.GetLayer("buildings")
    field_index = buildings_layer_copied.FindFieldIndex("heeft_adres", True)

    if field_index > 0:
        buildings_layer_copied.DeleteField(field_index)

    field_selection = []
    layer_def: ogr.FeatureDefn = buildings_layer_copied.GetLayerDefn()

    for i in range(layer_def.GetFieldCount()):
        field: ogr.FieldDefn = layer_def.GetFieldDefn(i)
        field_name = field.GetName()
        field_selection.append("buildings.{0} AS {0}".format(field_name))

    sql = """
    SELECT
        {0},
        adresses.pandidentificatie IS NOT NULL AS heeft_adres
    FROM
        buildings
        LEFT JOIN adresses ON buildings.identificatie = adresses.pandidentificatie
    """.format(",".join(field_selection))

    join_layer: ogr.Layer = memory_ds.ExecuteSQL(sql, dialect="OGRSQL")

    if not join_layer:
        raise ValueError("Problem with joining the layers.")

    updated_layer = buildings_ds.CopyLayer(join_layer,
                                           buildings_layer.GetName(),
                                           options=['OVERWRITE=YES'])

    if not updated_layer:
        raise ValueError("Problem with adding the required column.")

    buildings_layer = None
    adresses_layer = None
    updated_layer = None
    buildings_ds = None
    adresses_ds = None
    buildings_layer_copied = None
    memory_ds = None
