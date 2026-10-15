# SPDX-License-Identifier: GPL-2.0-or-later
"""Native geometry matching and explicit hierarchy placement for Data In."""
from pathlib import Path
from contextlib import closing
import sqlite3
import uuid

from qgis.core import (QgsCoordinateTransform, QgsGeometry, QgsProject,
                       QgsVectorLayer, QgsWkbTypes)
from . import hierarchy as store
from .farm_project import validate_farm
from .hierarchy_dialog import sync_tree

KINDS = ("organisation", "client", "farm", "field")


def workspace(project=None):
    project = project or QgsProject.instance()
    if not project.fileName():
        raise ValueError("Create or open an Ag Tech project first, then import your data.")
    root = Path(project.fileName()).resolve().parent
    info = validate_farm(root)
    if info["version"] != 2 or project.readEntry("AgTechTooling", "farm_id")[0] != info["farm_id"]:
        raise ValueError("Open a current Ag Tech workspace with Open Project before importing.")
    if any(getattr(layer, "isEditable", lambda: False)() for layer in project.mapLayers().values()):
        raise ValueError("Save or discard layer edits and leave editing mode before importing.")
    return root


def field_path(root, field_id):
    rows, result, selected = store.records(root), {}, field_id
    for kind in reversed(KINDS):
        row = next((r for r in rows[kind] if r["id"] == selected), None)
        if row is None:
            raise ValueError("The field hierarchy changed. Choose the destination again.")
        result[kind] = row["name"]
        selected = row.get(store.ENTITIES[kind][2])
    return result


def ensure_field(root, names):
    """Create only missing attribute records in one transaction (see TOOLING)."""
    names = {kind: store.text(names[kind]) for kind in KINDS}
    rows, parent_id = store.records(root), None
    try:
        with closing(sqlite3.connect(store.database(root).resolve().as_uri() + "?mode=rw", uri=True)) as connection:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                for kind in KINDS:
                    table, _, parent_key = store.ENTITIES[kind]
                    match = next((r for r in rows[kind] if r["name"].casefold() == names[kind].casefold()
                                  and (not parent_key or r[parent_key] == parent_id)), None)
                    if match:
                        parent_id = match["id"]
                        continue
                    identifier = str(uuid.uuid4())
                    columns = ["id", "name"] + ([parent_key] if parent_key else [])
                    values = [identifier, names[kind]] + ([parent_id] if parent_key else [])
                    connection.execute(f'INSERT INTO "{table}" ({",".join(columns)}) VALUES ({",".join("?" for v in values)})', values)
                    parent_id = identifier
    except sqlite3.Error as error:
        raise ValueError("Could not create the field hierarchy. No new records were saved: " + str(error)) from error
    return parent_id


def match_field(root, incoming, project=None):
    """Match entire geometries, never centroids, file names or bounding-box overlap."""
    project = project or QgsProject.instance()
    if isinstance(incoming, QgsVectorLayer) and incoming.geometryType() == QgsWkbTypes.NullGeometry:
        return {"field_id": None, "reason": "This table has no map geometry. Choose its field."}
    if not incoming.crs().isValid():
        return {"field_id": None, "reason": "This file has no recognised coordinate system. Select it before importing."}
    if isinstance(incoming, QgsVectorLayer):
        geometries = []
        for feature in incoming.getFeatures():
            geometry = feature.geometry()
            if geometry.isNull() or geometry.isEmpty() or not geometry.isGeosValid():
                return {"field_id": None, "reason": "Some features have missing or invalid geometry. Choose the field explicitly."}
            geometries.append(geometry)
            if len(geometries) > 10000:
                return {"field_id": None, "reason": "This dataset is too large for automatic placement. Choose its field."}
        if not geometries:
            return {"field_id": None, "reason": "This dataset is empty. Choose its field."}
        footprint = QgsGeometry.unaryUnion(geometries)
    else:
        footprint = QgsGeometry.fromRect(incoming.extent()).densifyByCount(8)
    if footprint.isNull() or footprint.isEmpty():
        return {"field_id": None, "reason": "Could not determine the full data footprint. Choose its field."}

    key = store.workspace_id(root)
    known_fields = {r["id"] for r in store.records(root)["field"]}
    boundaries = QgsVectorLayer(store.layer_uri(root, "agtech_boundaries"), "Field boundaries", "ogr")
    sources = [(boundaries, None)]
    sources += [(layer, str(layer.customProperty("AgTechTooling/import_field")))
                for layer in project.mapLayers().values()
                if isinstance(layer, QgsVectorLayer) and layer.id() != incoming.id()
                and layer.customProperty("AgTechTooling/workspace") == key
                and layer.customProperty("AgTechTooling/import_role") == "boundary"]
    shapes, unsafe = {}, False
    try:
        for layer, assigned in sources:
            if not layer.isValid() or not layer.crs().isValid():
                unsafe = True
                continue
            transform = QgsCoordinateTransform(layer.crs(), incoming.crs(), project.transformContext())
            for feature in layer.getFeatures():
                identifier = assigned or str(feature["field_id"])
                if identifier not in known_fields:
                    continue
                geometry = feature.geometry()
                if geometry.isNull() or geometry.isEmpty():
                    continue
                if not geometry.isGeosValid():
                    unsafe = True
                    continue
                geometry.transform(transform)
                if not geometry.isGeosValid():
                    unsafe = True
                    continue
                shapes.setdefault(identifier, []).append(geometry)
        matches = []
        for identifier, parts in shapes.items():
            boundary = QgsGeometry.unaryUnion(parts)
            if boundary.isNull() or boundary.isEmpty() or not boundary.isGeosValid():
                unsafe = True
                continue
            remainder = footprint.difference(boundary)
            # QGIS represents a successful empty point/line difference as null.
            # GEOS operation errors are exposed separately through lastError().
            if remainder.lastError():
                unsafe = True
            elif remainder.isEmpty():
                matches.append(identifier)
        if len(matches) == 1 and not unsafe:
            return {"field_id": matches[0], "reason": "All data fits within this field's boundary."}
        reason = ("More than one field boundary contains this data. Choose its field." if len(matches) > 1
                  else "No single field boundary contains all this data. Choose a field or create one below.")
        if unsafe:
            reason = "Some boundaries could not be checked safely. Choose the field explicitly."
        return {"field_id": None, "reason": reason}
    except Exception:
        return {"field_id": None, "reason": "The boundary comparison could not be completed. Choose the field explicitly."}


def place_layer(root, layer, field_id, role="data", project=None):
    project = project or QgsProject.instance()
    if role not in {"data", "boundary"} or (role == "boundary" and (
            not isinstance(layer, QgsVectorLayer) or layer.geometryType() != QgsWkbTypes.PolygonGeometry)):
        raise ValueError("Only polygon data can be used as a field boundary.")
    if field_id not in {r["id"] for r in store.records(root)["field"]}:
        raise ValueError("Select a valid field before importing.")
    _, groups = sync_tree(root, project)
    whole = groups["whole:" + field_id]
    group = next((n for n in whole.children() if n.customProperty("AgTechTooling/import_group") == field_id), None)
    if group is None:
        group = whole.addGroup("Imported Data")
        group.setCustomProperty("AgTechTooling/import_group", field_id)
    layer.setCustomProperty("AgTechTooling/workspace", store.workspace_id(root))
    layer.setCustomProperty("AgTechTooling/import_field", field_id)
    layer.setCustomProperty("AgTechTooling/import_role", role)
    if isinstance(layer, QgsVectorLayer):
        layer.setReadOnly(True)
    if layer.id() not in project.mapLayers():
        project.addMapLayer(layer, False)
    node = project.layerTreeRoot().findLayer(layer.id())
    if node is not None:
        group.addChildNode(node.clone())
        node.parent().removeChildNode(node)
    else:
        group.addLayer(layer)
    project.setDirty(True)
