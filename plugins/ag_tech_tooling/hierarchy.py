# SPDX-License-Identifier: GPL-2.0-or-later
"""Native QGIS tables and services for the organisation/client/farm/field model."""
from contextlib import closing
from datetime import date
from pathlib import Path
import sqlite3
import uuid

from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsFeature, QgsField, QgsProject, QgsProviderConnectionException, QgsProviderRegistry, QgsVectorFileWriter, QgsVectorLayer

ENTITIES = {
    "organisation": ("agtech_organisations", None, None),
    "client": ("agtech_clients", "organisation", "organisation_id"),
    "farm": ("agtech_farms", "client", "client_id"),
    "field": ("agtech_fields", "farm", "farm_id"),
    "season": ("agtech_seasons", "field", "field_id"),
    "crop": ("agtech_crops", "season", "season_id"),
}
SPATIAL = {"Boundaries": ("agtech_boundaries", "MultiPolygon"),
           "Guidance Lines": ("agtech_guidance", "MultiLineString"),
           "Infrastructure": ("agtech_infrastructure", "Point")}


def database(root):
    return Path(root) / "Data/farm.gpkg"


def layer_uri(root, table, subset=None):
    # Explicit normal locking on managed providers also prevents QGIS 3.44
    # from enabling WAL during a write while pooled readers use nolock mode.
    uri = f"{database(root)}|layername={table}|option:NOLOCK=NO"
    return uri + "|subset=" + subset if subset is not None else uri


def text(value):
    value = value.strip()
    if not value or len(value) > 120 or any(ord(char) < 32 for char in value):
        raise ValueError("Enter a name of 1–120 characters.")
    return value


def _write_table(path, table, fields, geometry="None", crs=None):
    uri = geometry if crs is None else f"{geometry}?crs={crs.authid()}"
    layer = QgsVectorLayer(uri, table, "memory")
    if not layer.isValid() or not layer.dataProvider().addAttributes([QgsField(name, QVariant.String) for name in fields]):
        raise ValueError(f"QGIS could not prepare {table}.")
    layer.updateFields()
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName, options.layerName = "GPKG", table
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    if geometry == "None":
        options.layerOptions = ["ASPATIAL_VARIANT=GPKG_ATTRIBUTES"]
    result = QgsVectorFileWriter.writeAsVectorFormatV3(layer, str(path), QgsProject.instance().transformContext(), options)
    if result[0] != QgsVectorFileWriter.NoError:
        raise ValueError(f"QGIS could not create {table}: {result[1]}")


def _connection(path):
    try:
        return QgsProviderRegistry.instance().providerMetadata("ogr").createConnection(str(path), {})
    except QgsProviderConnectionException as error:
        raise ValueError("QGIS could not open the workspace database: " + str(error)) from error


def _execute(connection, sql):
    try:
        return connection.executeSql(sql)
    except QgsProviderConnectionException as error:
        raise ValueError("QGIS could not initialise the hierarchy: " + str(error)) from error


def initialise(root, organisation, client, farm, farm_id, crs, field=None):
    """Called on a new or staged upgrade copy, never on the user's original."""
    path = database(root)
    reserved = {value[0] for value in ENTITIES.values()} | {value[0] for value in SPATIAL.values()}
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as existing:
        conflict = {row[0] for row in existing.execute("SELECT name FROM sqlite_master WHERE type='table'")} & reserved
    if conflict:
        raise ValueError("Existing data uses reserved hierarchy table names: " + ", ".join(sorted(conflict)))
    for kind, (table, parent, parent_key) in ENTITIES.items():
        fields = ["id", "name"] + ([parent_key] if parent_key else [])
        if kind == "season":
            fields += ["start_date", "end_date"]
        _write_table(path, table, fields)
    for table, geometry in SPATIAL.values():
        _write_table(path, table, ["id", "field_id", "name", "revision"], geometry, crs)
    connection = _connection(path)
    for kind, (table, parent, parent_key) in ENTITIES.items():
        _execute(connection, f'CREATE UNIQUE INDEX "{table}_id" ON "{table}" (id)')
        context = f'"{parent_key}",' if parent_key else ""
        _execute(connection, f'CREATE UNIQUE INDEX "{table}_name" ON "{table}" ({context}name COLLATE NOCASE)')
        # Triggers enforce parent links even for writers which do not enable SQLite foreign_keys.
        for event in ("INSERT", "UPDATE"):
            invalid = "NEW.id IS NULL OR trim(NEW.id)='' OR NEW.name IS NULL OR trim(NEW.name)=''"
            if parent_key:
                parent_table = ENTITIES[parent][0]
                invalid += f' OR NEW."{parent_key}" IS NULL OR NOT EXISTS (SELECT 1 FROM "{parent_table}" WHERE id=NEW."{parent_key}")'
            _execute(connection, f'''CREATE TRIGGER "{table}_{event.lower()}_valid" BEFORE {event} ON "{table}"
                WHEN {invalid} BEGIN SELECT RAISE(ABORT,'Invalid hierarchy identity, name or parent'); END''')
        children = [(child_table, key) for child_table, parent_kind, key in ENTITIES.values() if parent_kind == kind]
        if kind == "field":
            children += [(table_name, "field_id") for table_name, geometry in SPATIAL.values()]
        for child_table, key in children:
            for event in ("DELETE", "UPDATE OF id"):
                suffix = "delete" if event == "DELETE" else "id_update"
                _execute(connection, f'''CREATE TRIGGER "{table}_{child_table}_{suffix}" BEFORE {event} ON "{table}"
                    WHEN EXISTS (SELECT 1 FROM "{child_table}" WHERE "{key}"=OLD.id)
                    BEGIN SELECT RAISE(ABORT,'This record is referenced by child data'); END''')
    for table, geometry in SPATIAL.values():
        _execute(connection, f'CREATE UNIQUE INDEX "{table}_id" ON "{table}" (id)')
        for event in ("INSERT", "UPDATE"):
            _execute(connection, f'''CREATE TRIGGER "{table}_{event.lower()}_field" BEFORE {event} ON "{table}"
                WHEN NEW.id IS NULL OR trim(NEW.id)='' OR NEW.field_id IS NULL
                OR NOT EXISTS (SELECT 1 FROM agtech_fields WHERE id=NEW.field_id)
                BEGIN SELECT RAISE(ABORT,'Supply a feature identity and select a valid field'); END''')
    del connection
    organisation_id = add_record(root, "organisation", organisation)
    client_id = add_record(root, "client", client, organisation_id)
    add_record(root, "farm", farm, client_id, record_id=farm_id)
    if field and field.strip():
        add_record(root, "field", field, farm_id)


def records(root):
    result = {}
    with closing(sqlite3.connect(database(root).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        for kind, (table, _, _) in ENTITIES.items():
            result[kind] = [dict(row) for row in connection.execute(f'SELECT * FROM "{table}" ORDER BY name COLLATE NOCASE')]
    return result


def workspace_id(root):
    with closing(sqlite3.connect(database(root).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        value = connection.execute("SELECT farm_id FROM agtech_farm").fetchone()[0]
    uuid.UUID(value)
    return value


def validate(root):
    rows = records(root)
    for kind, items in rows.items():
        _, parent, parent_key = ENTITIES[kind]
        parents = {row["id"] for row in rows[parent]} if parent else None
        seen = set()
        for row in items:
            uuid.UUID(row["id"])
            text(row["name"])
            if parent and row[parent_key] not in parents:
                raise ValueError(f"A {kind} references a missing {parent}.")
            key = (row.get(parent_key), row["name"].casefold())
            if key in seen:
                raise ValueError(f"Duplicate {kind} name within the same parent.")
            seen.add(key)
            if kind == "season":
                validate_dates(row["start_date"], row["end_date"])
    if not rows["organisation"]:
        raise ValueError("This workspace has no organisation.")
    for table, geometry in SPATIAL.values():
        layer = QgsVectorLayer(layer_uri(root, table), table, "ogr")
        if not layer.isValid():
            raise ValueError(f"Missing or invalid {table} layer.")
    return rows


def validate_dates(start, end):
    if start:
        date.fromisoformat(start)
    if end:
        date.fromisoformat(end)
    if start and end and start > end:
        raise ValueError("The season end date must follow its start date.")


def add_record(root, kind, name, parent_id=None, record_id=None, start="", end=""):
    name = text(name)
    table, parent, parent_key = ENTITIES[kind]
    existing = records(root)
    if parent and parent_id not in {row["id"] for row in existing[parent]}:
        raise ValueError(f"Select a {parent} before adding a {kind}.")
    if any(row["name"].casefold() == name.casefold() and (not parent or row[parent_key] == parent_id)
           for row in existing[kind]):
        raise ValueError(f"That {kind} name already exists under this parent.")
    if kind == "season":
        validate_dates(start, end)
    record_id = record_id or str(uuid.uuid4())
    uuid.UUID(record_id)
    layer = QgsVectorLayer(layer_uri(root, table), table, "ogr")
    feature = QgsFeature(layer.fields())
    values = {"id": record_id, "name": name}
    if parent_key:
        values[parent_key] = parent_id
    if kind == "season":
        values.update(start_date=start, end_date=end)
    for key, value in values.items():
        feature[key] = value
    if not layer.dataProvider().addFeatures([feature])[0]:
        raise ValueError(f"QGIS could not save the {kind}. No parent records were changed.")
    return record_id


def rename_record(root, kind, record_id, name):
    name = text(name)
    rows = records(root)[kind]
    row = next((row for row in rows if row["id"] == record_id), None)
    if row is None:
        raise ValueError("The selected record no longer exists.")
    parent_key = ENTITIES[kind][2]
    if any(other["id"] != record_id and other["name"].casefold() == name.casefold()
           and (not parent_key or other[parent_key] == row[parent_key]) for other in rows):
        raise ValueError("That name is already used under the same parent.")
    layer = QgsVectorLayer(layer_uri(root, ENTITIES[kind][0]), kind, "ogr")
    feature = next((feature for feature in layer.getFeatures() if feature["id"] == record_id), None)
    if feature is None or not layer.dataProvider().changeAttributeValues({feature.id(): {layer.fields().indexFromName("name"): name}}):
        raise ValueError("QGIS could not rename the selected record.")
