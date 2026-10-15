# SPDX-License-Identifier: GPL-2.0-or-later
"""One-click starter workspace in the operating system's Documents location."""
from pathlib import Path
from qgis.PyQt.QtCore import QStandardPaths
from qgis.core import QgsCoordinateReferenceSystem, QgsProject
from .farm_project import create_farm
from . import hierarchy as store


def projects_directory():
    documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    if not documents:
        raise ValueError("Windows could not locate Documents. Use New Project with Options to choose a location.")
    return Path(documents) / "Ag Tech Tooling" / "Projects"


def create_default(parent=None, crs=None):
    parent = Path(parent) if parent is not None else projects_directory()
    parent.mkdir(parents=True, exist_ok=True)
    name, number = "My Farm Data", 1
    while (parent / name).exists():
        number += 1
        name = f"My Farm Data {number}"
    crs = crs or QgsProject.instance().crs()
    if not crs.isValid() or not crs.authid():
        crs = QgsCoordinateReferenceSystem("EPSG:4326")
    root = create_farm(parent, name, crs, organisation="Organisation 1", client="Client 1",
                       farm="Farm 1", field="Field 1", default_season="Season 1", build_tree=True)
    # Open providers only at their final location, so no cached data source points into staging.
    from .hierarchy_dialog import show_field
    project = QgsProject()
    try:
        if not project.read(str(root / "Farm.qgz")):
            raise ValueError(f"Created {root}, but QGIS could not prepare the initial map.")
        show_field(root, store.records(root)["field"][0]["id"], project=project)
        if not project.write():
            raise ValueError(f"Created {root}, but QGIS could not save the initial map.")
    finally:
        project.clear()
    return root
