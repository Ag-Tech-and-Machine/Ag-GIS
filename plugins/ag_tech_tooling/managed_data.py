# SPDX-License-Identifier: GPL-2.0-or-later
"""Managed copies and an additive GeoPackage dataset catalogue, using native writers."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import uuid
from qgis.PyQt.QtCore import QThread

from qgis.core import (QgsCoordinateReferenceSystem, QgsDefaultValue, QgsFeature, QgsMapLayerStyle,
    QgsProject, QgsProviderRegistry, QgsRasterBlockFeedback, QgsRasterFileWriter,
    QgsRasterLayer, QgsRasterPipe, QgsVectorFileWriter, QgsVectorLayer)
from . import hierarchy as store
from . import data_types

TABLE = "agtech_datasets"
FIELDS = ("id", "field_id", "name", "role", "layer_type", "provider", "uri", "crs_wkt",
          "source_uri", "source_hash", "created_utc", "style_xml", "catalog_version")


def _companions(path):
    found = []
    for suffix in (".aux.xml", ".vat.dbf"):
        candidate = Path(str(path) + suffix)
        if candidate.is_file():
            found.append((candidate, "append", suffix))
    for suffix in (".tfw", ".tifw", ".tiffw", ".wld", ".prj"):
        candidate = path.with_suffix(suffix)
        if candidate.is_file():
            found.append((candidate, "replace", ".tifw" if suffix == ".tiffw" else suffix))
    return found


def _cancel(feedback):
    app = QgsProject.instance().thread()
    if feedback and QThread.currentThread() == app:
        from qgis.core import QgsApplication
        QgsApplication.processEvents()
    if feedback and feedback.isCanceled():
        raise ValueError("Import stopped. This dataset was not saved.")


def records(root):
    with closing(sqlite3.connect(store.database(root).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)).fetchone():
            return []
        columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{TABLE}")')}
        if not set(FIELDS).issubset(columns):
            raise ValueError("The dataset catalogue is incompatible; it has not been changed.")
        connection.row_factory = sqlite3.Row
        rows = [dict(row) for row in connection.execute(f'SELECT * FROM "{TABLE}" ORDER BY created_utc,id')]
    if any(row["catalog_version"] != "1" for row in rows):
        raise ValueError("This dataset catalogue needs a compatible plugin version.")
    return rows


def _catalogue(root):
    existing = records(root)
    with closing(sqlite3.connect(store.database(root).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        present = connection.execute("SELECT 1 FROM sqlite_master WHERE name=?", (TABLE,)).fetchone()
    if not present:
        store._write_table(store.database(root), TABLE, FIELDS)
        connection = store._connection(store.database(root))
        connection.executeSql(f'CREATE UNIQUE INDEX "agtech_dataset_ids" ON "{TABLE}" (id)')
        connection.executeSql(f'''CREATE TRIGGER agtech_dataset_field BEFORE INSERT ON "{TABLE}"
            WHEN NOT EXISTS(SELECT 1 FROM agtech_fields WHERE id=NEW.field_id)
            BEGIN SELECT RAISE(ABORT,'Select a valid field for this dataset'); END''')
        connection.executeSql('''CREATE TRIGGER agtech_fields_datasets_delete BEFORE DELETE ON agtech_fields
            WHEN EXISTS(SELECT 1 FROM agtech_datasets WHERE field_id=OLD.id)
            BEGIN SELECT RAISE(ABORT,'This field contains saved datasets'); END''')
    return existing


def source_hash(layer, feedback=None):
    """Hash original file bundles (including shapefile sidecars), or vector content."""
    decoded = QgsProviderRegistry.instance().decodeUri(layer.providerType(), layer.source())
    path = Path(decoded.get("path") or "")
    if not isinstance(layer, QgsVectorLayer) and path.suffix.lower() == ".vrt":
        return ""  # The XML can stay unchanged while its referenced pixels change.
    paths = []
    if path.is_file():
        paths = [path]
        if path.suffix.lower() == ".shp":
            paths = sorted(p for p in path.parent.iterdir() if p.stem.casefold() == path.stem.casefold()
                           and p.suffix.lower() in {".shp", ".shx", ".dbf", ".prj", ".qpj", ".cpg"})
        elif path.suffix.lower() in {".gpkg", ".sqlite", ".db"}:
            journal = Path(str(path) + "-wal")
            if journal.is_file():
                paths.append(journal)
        elif path.suffix.lower() in {".tif", ".tiff"}:
            paths += [p for p, _, _ in _companions(path)]
        elif not isinstance(layer, QgsVectorLayer):
            paths += [p for p in (Path(str(path) + ".aux.xml"), path.with_suffix(".prj"),
                      path.with_suffix(".wld"), path.with_suffix(".pgw"), path.with_suffix(".jgw"),
                      path.with_suffix(".ige")) if p.is_file()]
    digest = hashlib.sha256()
    digest.update(layer.crs().toWkt().encode())
    if paths:
        for item in paths:
            _cancel(feedback)
            digest.update(item.suffix.lower().encode())
            with item.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    _cancel(feedback)
                    digest.update(block)
    elif isinstance(layer, QgsVectorLayer):
        digest.update(str([(f.name(), f.typeName()) for f in layer.fields()]).encode())
        for feature in layer.getFeatures():
            _cancel(feedback)
            digest.update(bytes(feature.geometry().asWkb()))
            digest.update(json.dumps(feature.attributes(), default=str).encode())
    else:
        # A remote/virtual raster has no verified content identity: don't deduplicate it.
        return ""
    return digest.hexdigest()


def dataset_uri(root, record):
    relative, _, options = record["uri"].partition("|")
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("Dataset catalogue contains a path outside this workspace.")
    return str(path) + ("|" + options if options else "")


def open_dataset(root, record):
    factory = QgsVectorLayer if record["layer_type"] == "vector" else QgsRasterLayer
    layer = factory(dataset_uri(root, record), record["name"], record["provider"])
    if not layer.isValid():
        raise ValueError("Saved dataset is missing or unreadable: " + record["name"])
    layer.setCrs(QgsCoordinateReferenceSystem.fromWkt(record["crs_wkt"]))
    if record.get("style_xml"):
        QgsMapLayerStyle(record["style_xml"]).writeToLayer(layer)
    from .dataset_styles import restore
    restore(root, record, layer)
    layer.setCustomProperty("AgTechTooling/dataset_id", record["id"])
    layer.setCustomProperty("AgTechTooling/import_source", record["source_uri"])
    if record.get("classification_id"):
        from .reviewed_import import read_binding
        binding = read_binding(root, record)
        layer.setCustomProperty("AgTechTooling/import_season", binding["season_id"])
        layer.setCustomProperty("AgTechTooling/classification_id", record["classification_id"])
    return layer


def _same_number(left, right):
    return (math.isnan(left) and math.isnan(right)) or left == right


def _raster_copy(source, output, feedback):
    path = Path(source.source())
    from osgeo import gdal
    original = gdal.OpenEx(source.source(), gdal.OF_RASTER)
    if original is None:
        raise ValueError("Could not inspect raster georeferencing and units before saving.")
    transform = original.GetGeoTransform(can_return_null=True)
    gcps = original.GetGCPCount()
    metadata = original.GetMetadata()
    bands = [{"metadata": original.GetRasterBand(b).GetMetadata(),
              "unit": original.GetRasterBand(b).GetUnitType(),
              "description": original.GetRasterBand(b).GetDescription(),
              "colour": original.GetRasterBand(b).GetColorInterpretation(),
              "categories": original.GetRasterBand(b).GetCategoryNames(),
              "palette": original.GetRasterBand(b).GetColorTable().Clone()
                  if original.GetRasterBand(b).GetColorTable() else None}
             for b in range(1, original.RasterCount + 1)]
    original = None
    if transform is None and not gcps:
        raise ValueError("This raster is not georeferenced. Use the Georeferencer in the full tools before importing it onto the map.")
    if path.is_file() and path.suffix.lower() in {".tif", ".tiff"}:
        # Byte-for-byte GeoTIFF copies preserve numeric precision, scale, units,
        # band metadata and colour interpretation without a render/export step.
        pairs = [(path, output)]
        for original, mode, suffix in _companions(path):
            pairs.append((original, Path(str(output) + suffix) if mode == "append" else output.with_suffix(suffix)))
        for original, saved in pairs:
            with original.open("rb") as reader, saved.open("xb") as writer:
                for block in iter(lambda: reader.read(1024 * 1024), b""):
                    _cancel(feedback)
                    writer.write(block)
    else:
        provider = source.dataProvider()
        if gcps or transform is None or transform[2] != 0 or transform[4] != 0:
            raise ValueError("This raster needs georeferencing conversion. Save a georeferenced lossless GeoTIFF first.")
        if any(provider.bandScale(b) != 1 or provider.bandOffset(b) != 0 for b in range(1, source.bandCount() + 1)):
            raise ValueError("This raster has scale/offset metadata. Export a lossless GeoTIFF first to preserve it.")
        pipe = QgsRasterPipe()
        if not pipe.set(provider.clone()):
            raise ValueError("Ag-GIS could not prepare this raster.")
        writer = QgsRasterFileWriter(str(output))
        writer.setOutputFormat("GTiff")
        writer.setCreateOptions(["COMPRESS=DEFLATE", "TILED=YES", "BIGTIFF=IF_SAFER"])
        error = writer.writeRaster(pipe, source.width(), source.height(), source.extent(), source.crs(),
                                   QgsProject.instance().transformContext(), feedback)
        if int(error) != 0:
            raise ValueError("Ag-GIS could not save the raster (code " + str(int(error)) + ").")
        # Transfer metadata missing from the QGIS writer API, without changing pixels.
        target = gdal.OpenEx(str(output), gdal.OF_RASTER | gdal.OF_UPDATE)
        if target is None:
            raise ValueError("Could not preserve raster metadata in the saved copy.")
        target.SetMetadata(metadata)
        for index, info in enumerate(bands, 1):
            band = target.GetRasterBand(index)
            band.SetMetadata(info["metadata"])
            band.SetUnitType(info["unit"])
            band.SetDescription(info["description"])
            if info["palette"] is not None:
                band.SetColorTable(info["palette"])
            if info["categories"]:
                band.SetCategoryNames(info["categories"])
            band.SetColorInterpretation(info["colour"])
        band, target = None, None
    _cancel(feedback)
    saved = QgsRasterLayer(str(output), source.name(), "gdal")
    problem = _raster_problem(source, saved)
    saved = None  # Close the validation reader before any failed-copy cleanup on Windows.
    if problem:
        raise ValueError(problem)


def _raster_problem(source, saved):
    if not saved.isValid() or (saved.width(), saved.height(), saved.bandCount()) != (source.width(), source.height(), source.bandCount()):
        return "Saved raster dimensions or bands did not match the source."
    for band in range(1, source.bandCount() + 1):
        before, after = source.dataProvider(), saved.dataProvider()
        if (before.dataType(band) != after.dataType(band)
                or before.sourceHasNoDataValue(band) != after.sourceHasNoDataValue(band)
                or before.bandScale(band) != after.bandScale(band)
                or before.bandOffset(band) != after.bandOffset(band)):
            return "Raster conversion changed numeric metadata; import was not saved."
        if before.sourceHasNoDataValue(band) and not _same_number(before.sourceNoDataValue(band), after.sourceNoDataValue(band)):
            return "Raster conversion changed NoData; import was not saved."
    if saved.extent() != source.extent():
        return "Raster georeferencing did not match; import was not saved."
    return None


def save_dataset(root, source, field_id, role="data", feedback=None, *, review=None):
    """Save one complete dataset before registering it. Originals are never edited."""
    feedback = feedback or QgsRasterBlockFeedback()
    root = Path(root).resolve()
    if not store.database(root).resolve().is_relative_to(root):
        raise ValueError("Managed data must be saved inside its workspace.")
    decoded = QgsProviderRegistry.instance().decodeUri(source.providerType(), source.source())
    if decoded.get("path") and Path(decoded["path"]).resolve() == store.database(root).resolve():
        raise ValueError("This is already workspace data. Use Open Project or Filter Data rather than importing its own GeoPackage.")
    data_types.validate(source, role)
    if field_id not in {r["id"] for r in store.records(root)["field"]}:
        raise ValueError("Select a valid field before saving data.")
    _cancel(feedback)
    from .reviewed_import import validate_review, read_binding, store_review
    if review is not None:
        validate_review(root, source, field_id, role, review)
    digest = source_hash(source, feedback)
    existing = records(root)
    duplicate = next((r for r in existing if digest and r["source_uri"] == source.source()
                      and r["source_hash"] == digest and r["field_id"] == field_id and r["role"] == role), None)
    if duplicate:
        previous_review = read_binding(root, duplicate)
        if previous_review != review:
            raise ValueError("This dataset is already saved with a different job context. Existing history was not reassigned.")
        return duplicate, open_dataset(root, duplicate), False
    identifier = uuid.uuid4().hex
    table, output = "agtech_data_" + identifier, None
    vector = isinstance(source, QgsVectorLayer)
    style = QgsMapLayerStyle()
    style.readFromLayer(source)
    record = dict(id=identifier, field_id=field_id, name=source.name(), role=role,
        layer_type="vector" if vector else "raster", provider="ogr" if vector else "gdal",
        crs_wkt=source.crs().toWkt(), source_uri=source.source(), source_hash=digest,
        created_utc=datetime.now(timezone.utc).isoformat(), style_xml=style.xmlData(), catalog_version="1")
    saved, catalog, feature, vector_started = None, None, None, False
    try:
        if vector:
            with closing(sqlite3.connect(store.database(root).as_uri() + "?mode=ro", uri=True)) as check:
                if check.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone():
                    raise ValueError("The generated dataset name is already used. Import again.")
            vector_started = True
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName, options.layerName = "GPKG", table
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            options.feedback, options.includeZ = feedback, True
            names = {f.name().casefold() for f in source.fields()}
            primary = "_agtech_fid"
            while primary.casefold() in names:
                primary += "_"
            geometry = "_agtech_geometry"
            while geometry.casefold() in names:
                geometry += "_"
            options.layerOptions = ["FID=" + primary, "GEOMETRY_NAME=" + geometry]
            result = QgsVectorFileWriter.writeAsVectorFormatV3(source, str(store.database(root)),
                        QgsProject.instance().transformContext(), options)
            if result[0] != QgsVectorFileWriter.NoError:
                raise ValueError("Ag-GIS could not save vector data: " + str(result[1]))
            record["uri"] = f"Data/farm.gpkg|layername={table}|option:NOLOCK=NO"
        else:
            folder = Path(root) / "Data/Rasters"
            if not folder.resolve().is_relative_to(root):
                raise ValueError("The raster folder points outside this workspace.")
            folder.mkdir(exist_ok=True)
            candidate = folder / (identifier + ".tif")
            if list(folder.glob(identifier + ".*")):
                raise ValueError("The generated raster name is already used. Import again.")
            output = candidate
            _raster_copy(source, output, feedback)
            record["uri"] = output.relative_to(root).as_posix()
        _cancel(feedback)
        saved = open_dataset(root, record)
        if vector and (saved.featureCount() != source.featureCount()
                       or not set(source.fields().names()).issubset(saved.fields().names())):
            del saved
            raise ValueError("Saved vector counts or attributes did not match; import was not saved.")
        # Catch a changed local source before declaring its managed copy complete.
        if digest and source_hash(source, feedback) != digest:
            del saved
            raise ValueError("Source changed during import. Retry once the source is stable.")
        _catalogue(root)
        if review is None:
            catalog = QgsVectorLayer(store.layer_uri(root, TABLE), "Datasets", "ogr")
            feature = QgsFeature(catalog.fields())
            for key, value in record.items():
                feature[key] = value
            if not catalog.dataProvider().addFeatures([feature])[0]:
                del saved
                raise ValueError("Could not register the saved dataset.")
        else:
            _cancel(feedback)
            with closing(sqlite3.connect(store.database(root).as_uri() + "?mode=rw", uri=True)) as connection:
                connection.execute("PRAGMA foreign_keys=ON")
                with connection:
                    connection.execute("BEGIN IMMEDIATE")
                    validate_review(root, source, field_id, role, review, connection=connection)
                    connection.execute(f'INSERT INTO "{TABLE}" ({",".join(FIELDS)}) VALUES ({",".join("?" for _ in FIELDS)})',
                                       [record[key] for key in FIELDS])
                    record["classification_id"] = store_review(connection, record, review)
                    # Last gate before metadata commit: no Qt event pumping here.
                    validate_review(root, source, field_id, role, review, connection=connection)
            saved.setCustomProperty("AgTechTooling/import_season", review["season_id"])
            saved.setCustomProperty("AgTechTooling/classification_id", record["classification_id"])
        return record, saved, True
    except Exception:
        saved, catalog, feature = None, None, None
        if vector and vector_started:
            connection = store._connection(store.database(root))
            # Native provider cleanup also removes GeoPackage geometry metadata.
            with closing(sqlite3.connect(store.database(root).resolve().as_uri() + "?mode=ro", uri=True)) as check:
                present = check.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone()
            if present:
                connection.dropVectorTable("", table)
        elif output is not None:
            for file in output.parent.glob(output.stem + ".*"):
                if file.resolve().parent == output.parent.resolve():
                    file.unlink(missing_ok=True)
        raise


def apply_filters(root, field_id="*", role="*", project=None):
    """Filter imports and native references, preserving unrelated layers and checkbox choices."""
    project = project or QgsProject.instance()
    if field_id != "*" and field_id not in {r["id"] for r in store.records(root)["field"]}:
        raise ValueError("Choose a valid field filter.")
    if role != "*" and role not in data_types.TYPES:
        raise ValueError("Choose a valid data-type filter.")
    if any(getattr(layer, "isEditable", lambda: False)() for layer in project.mapLayers().values()):
        raise ValueError("Finish layer edits before changing data filters.")
    key = store.workspace_id(root)
    native_roles = {"agtech_boundaries": "boundary", "agtech_guidance": "guidance", "agtech_infrastructure": "assets"}
    from .hierarchy_dialog import sync_tree
    group, groups = sync_tree(root, project)
    aggregate = next((node for node in group.children() if node.customProperty("AgTechTooling/aggregate")), None)
    for layer in project.mapLayers().values():
        if layer.customProperty("AgTechTooling/workspace") != key:
            continue
        table = layer.customProperty("AgTechTooling/table", "")
        imported = bool(layer.customProperty("AgTechTooling/import_field"))
        if not imported and table not in native_roles:
            continue
        node = project.layerTreeRoot().findLayer(layer.id())
        if node is None:
            continue
        if table in native_roles:
            subset = "" if field_id == "*" else f'"field_id" = \'{field_id}\''
            if not layer.setSubsetString(subset):
                raise ValueError("Ag-GIS could not filter the native reference layer.")
            if field_id == "*":
                if aggregate is None:
                    aggregate = group.addGroup("All Fields")
                    aggregate.setCustomProperty("AgTechTooling/aggregate", True)
                parent = aggregate
                if not layer.customProperty("AgTechTooling/all_readonly", False):
                    layer.setCustomProperty("AgTechTooling/before_all_readonly", layer.readOnly())
                layer.setCustomProperty("AgTechTooling/all_readonly", True)
                layer.setReadOnly(True)
            else:
                parent = groups["whole:" + field_id]
                if layer.customProperty("AgTechTooling/all_readonly", False):
                    layer.setReadOnly(bool(layer.customProperty("AgTechTooling/before_all_readonly", False)))
                    layer.removeCustomProperty("AgTechTooling/all_readonly")
                for name, expression in (("id", "uuid()"), ("field_id", f"'{field_id}'"), ("revision", "'1'")):
                    layer.setDefaultValueDefinition(layer.fields().indexFromName(name), QgsDefaultValue(expression))
            if node.parent() is not parent:
                copy = node.clone()
                parent.addChildNode(copy)
                node.parent().removeChildNode(node)
                node = copy
            visible = role == "*" or role == native_roles[table]
        else:
            visible = (field_id == "*" or layer.customProperty("AgTechTooling/import_field") == field_id) and (
                        role == "*" or layer.customProperty("AgTechTooling/import_role") == role)
        hidden = bool(node.customProperty("AgTechTooling/filter_hidden", False))
        if not visible:
            if not hidden:
                node.setCustomProperty("AgTechTooling/pre_filter_checked", node.itemVisibilityChecked())
            node.setItemVisibilityChecked(False)
            node.setCustomProperty("AgTechTooling/filter_hidden", True)
        elif hidden:
            node.setItemVisibilityChecked(bool(node.customProperty("AgTechTooling/pre_filter_checked", True)))
            node.removeCustomProperty("AgTechTooling/filter_hidden")
    if aggregate is not None and not aggregate.children():
        group.removeChildNode(aggregate)
    if field_id != "*":
        project.writeEntry("AgTechTooling", "selected_field", field_id)
    project.writeEntry("AgTechTooling", "data_filter_field", field_id)
    project.writeEntry("AgTechTooling", "data_filter_role", role)
    sync_reference_visibility(project)
    project.setDirty(True)


def sync_reference_visibility(project=None):
    """Limit shared All Fields references to checked Whole Field branches.

    These native tables live outside the individual field groups, so QGIS cannot
    inherit their checks directly. Only owned, aggregate reference subsets change;
    layer checks, explicit Filter Data and all original GeoPackage rows stay intact.
    """
    project = project or QgsProject.instance()
    if project.readEntry("AgTechTooling", "data_filter_field")[0] != "*":
        return
    key = project.readEntry("AgTechTooling", "farm_id")[0]
    tree = project.layerTreeRoot()
    workspace = next((node for node in tree.children()
                      if node.customProperty("AgTechTooling/workspace", "") == key), None)
    groups = [node for node in workspace.findGroups(True)
              if node.customProperty("AgTechTooling/kind", "") == "whole"] if workspace else []
    if not key or not groups:
        return
    visible = sorted(str(node.customProperty("AgTechTooling/field"))
                     for node in groups if node.isVisible())
    from qgis.core import QgsExpression
    subset = ("" if len(visible) == len(groups) else
              '"field_id" IN (' + ",".join(QgsExpression.quotedString(value) for value in visible) + ")"
              if visible else "1=0")
    for layer in project.mapLayers().values():
        if (layer.customProperty("AgTechTooling/workspace", "") == key
                and layer.customProperty("AgTechTooling/all_readonly", False)
                and layer.customProperty("AgTechTooling/table", "") in
                {"agtech_boundaries", "agtech_guidance", "agtech_infrastructure"}
                and not layer.isEditable() and layer.subsetString() != subset):
            if not layer.setSubsetString(subset):
                raise ValueError("Ag-GIS could not update checked field references.")
            layer.triggerRepaint()


def restore_datasets(root, project=None):
    from .import_placement import place_layer
    project = project or QgsProject.instance()
    present = {str(layer.customProperty("AgTechTooling/dataset_id")) for layer in project.mapLayers().values()}
    failures = []
    rows = records(root)
    if not rows:
        return []
    for record in rows:
        if record["id"] in present:
            continue
        try:
            layer = open_dataset(root, record)
            place_layer(root, layer, record["field_id"], record["role"], project)
        except (ValueError, RuntimeError) as error:
            failures.append(str(error))
    apply_filters(root, project.readEntry("AgTechTooling", "data_filter_field", "*")[0],
                  project.readEntry("AgTechTooling", "data_filter_role", "*")[0], project)
    return failures
