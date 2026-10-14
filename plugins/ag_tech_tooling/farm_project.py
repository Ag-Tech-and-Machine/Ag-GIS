# SPDX-License-Identifier: GPL-2.0-or-later
"""Small, versioned farm workspace foundation; no agricultural schema yet."""
from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import uuid

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    Qgis, QgsCoordinateReferenceSystem, QgsFeature, QgsField,
    QgsProject, QgsVectorFileWriter, QgsVectorLayer,
)

SCHEMA_VERSION = 1
TABLE = "agtech_farm"


def validate_name(name):
    name = name.strip()
    if (not name or len(name) > 100 or re.search(r'[<>:"/\\|?*\x00-\x1f]', name)
            or name.endswith((".", " ")) or name in {".", ".."}
            or re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", name)):
        raise ValueError("Use a farm name of 1–100 characters without reserved filename characters.")
    return name


def create_farm(parent, name, crs):
    """Create in a sibling staging directory; never replace an existing farm."""
    name = validate_name(name)
    parent = Path(parent).resolve(strict=True)
    if not parent.is_dir():
        raise ValueError("Choose an existing folder for the farm.")
    if not crs.isValid() or not crs.authid():
        raise ValueError("Choose a recognised coordinate reference system for this farm.")
    destination = parent / name
    if destination.exists():
        raise ValueError("That farm folder already exists. Choose another name or open it instead.")
    staging = Path(tempfile.mkdtemp(prefix=".agtech-create-", dir=str(parent)))
    try:
        data = staging / "Data"
        data.mkdir()
        values = {
            "farm_id": str(uuid.uuid4()), "farm_name": name,
            "schema_version": str(SCHEMA_VERSION), "crs_authid": crs.authid(),
            "created_utc": datetime.now(timezone.utc).isoformat(),
        }
        layer = QgsVectorLayer("None", TABLE, "memory")
        provider = layer.dataProvider()
        if not provider.addAttributes([QgsField(key, QVariant.String) for key in values]):
            raise ValueError("Could not define the farm information fields.")
        layer.updateFields()
        feature = QgsFeature(layer.fields())
        feature.setAttributes(list(values.values()))
        if not provider.addFeatures([feature])[0]:
            raise ValueError("Could not prepare farm information.")
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = TABLE
        options.fileEncoding = "UTF-8"
        options.layerOptions = ["ASPATIAL_VARIANT=GPKG_ATTRIBUTES"]
        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer, str(data / "farm.gpkg"), QgsProject.instance().transformContext(), options)
        if result[0] != QgsVectorFileWriter.NoError:
            raise ValueError(f"QGIS could not write the farm GeoPackage: {result[1]}")
        project = QgsProject()
        project.setTitle(name)
        project.setCrs(crs)
        project.setFilePathStorage(Qgis.FilePathType.Relative)
        project.setFileName(str(staging / "Farm.qgz"))
        project.writeEntry("AgTechTooling", "farm_id", values["farm_id"])
        project.writeEntry("AgTechTooling", "schema_version", SCHEMA_VERSION)
        project.writeEntry("AgTechTooling", "database", "Data/farm.gpkg")
        if not project.write():
            raise ValueError("Could not save the farm map project.")
        del project
        validate_farm(staging)
        # Windows rename refuses an existing destination, including an empty folder.
        staging.rename(destination)
        return destination
    finally:
        if staging.exists():
            if staging.resolve().parent != parent or not staging.name.startswith(".agtech-create-"):
                raise RuntimeError("Refusing to clean an unexpected staging location.")
            shutil.rmtree(staging)


def validate_farm(root):
    """Read-only preflight; reject unrecognised/newer schemas without modifying them."""
    root = Path(root).resolve(strict=True)
    database = root / "Data" / "farm.gpkg"
    project_path = root / "Farm.qgz"
    if not database.is_file() or not project_path.is_file():
        raise ValueError("This farm needs Farm.qgz and Data/farm.gpkg. Restore missing files from backup.")
    if not database.resolve().is_relative_to(root):
        raise ValueError("The farm database must be stored inside its farm folder.")
    try:
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
            if connection.execute("PRAGMA application_id").fetchone()[0] != 0x47504B47:
                raise ValueError("The farm database is not a recognised GeoPackage.")
            rows = connection.execute(
                f"SELECT farm_id, farm_name, schema_version, crs_authid, created_utc FROM {TABLE}"
            ).fetchall()
            registered = connection.execute(
                "SELECT data_type FROM gpkg_contents WHERE table_name=?", (TABLE,)
            ).fetchone()
        if len(rows) != 1 or registered != ("attributes",):
            raise ValueError("The farm information table is missing or invalid.")
        farm_id, name, version, authid, created = rows[0]
        uuid.UUID(farm_id)
        if version != str(SCHEMA_VERSION):
            raise ValueError(f"Unsupported farm schema {version}; this plugin supports {SCHEMA_VERSION}. No changes made.")
        crs = QgsCoordinateReferenceSystem(authid)
        if not name or not created or not crs.isValid():
            raise ValueError("The farm settings are incomplete or invalid.")
        project = QgsProject()
        if not project.read(str(project_path)):
            raise ValueError("The farm map project cannot be read. Restore it from backup.")
        if project.readEntry("AgTechTooling", "farm_id")[0] != farm_id:
            raise ValueError("The map project and farm database belong to different farms.")
        if project.readNumEntry("AgTechTooling", "schema_version")[0] != SCHEMA_VERSION:
            raise ValueError("The map project schema is not supported.")
        if project.readEntry("AgTechTooling", "database")[0] != "Data/farm.gpkg":
            raise ValueError("The farm database location is not supported.")
        if project.crs() != crs:
            raise ValueError("The map and farm coordinate systems disagree. No changes made.")
        invalid = [layer.name() for layer in project.mapLayers().values() if not layer.isValid()]
        if invalid:
            raise ValueError("Missing or invalid layers: " + ", ".join(invalid))
        return {"name": name, "farm_id": farm_id, "crs": authid, "project": str(project_path)}
    except (sqlite3.Error, TypeError, AttributeError) as error:
        raise ValueError("The farm GeoPackage is incomplete or unreadable.") from error
