"""Esri catalogue upgrade preserves saved visibility, deletions and custom sources."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.core import QgsApplication, QgsProject, QgsDataSourceUri
from ag_tech_tooling.background_maps import ensure_background, background_layers, PROVIDERS, CATALOG_VERSION
from ag_tech_tooling.view_settings import ViewSettingsDialog

app = QgsApplication([], False)
app.initQgis()
project = QgsProject.instance()
try:
    project.writeEntry("AgTechTooling", "schema_version", 2)
    project.writeEntry("AgTechTooling", "view/background", "osm")
    ensure_background()
    layers = background_layers()
    assert "esri_world" in layers, "Esri World Imagery must be preconfigured in new maps"
    uri = QgsDataSourceUri()
    uri.setEncodedUri(layers["esri_world"].source())
    assert uri.param("url") == "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    assert uri.param("zmax") == "23" and layers["esri_world"].isValid()
    assert "Powered by Esri" in layers["esri_world"].metadata().rights()[0]
    assert "terms" in PROVIDERS["esri_world"]["description"].lower()
    dialog = ViewSettingsDialog()
    assert dialog.background.findData("esri_world") >= 0
    dialog.reject()
    tree = project.layerTreeRoot()
    node = lambda key: tree.findLayer(background_layers()[key].id())
    group = node("osm").parent()
    node("satellite_au").setItemVisibilityChecked(True)
    # Upgrade an existing v1 map, retaining its chosen map and a removed option.
    project.removeMapLayers([layers["esri_world"].id(), layers["satellite_world"].id()])
    project.writeEntry("AgTechTooling", "background_catalog_version", 1)
    existing = {key: layer.id() for key, layer in background_layers().items()}
    ensure_background()
    assert "esri_world" in background_layers()
    assert "satellite_world" not in background_layers(), "Upgrade must not restore deliberately removed old backgrounds"
    assert node("satellite_au").isVisible() and not node("esri_world").itemVisibilityChecked(), "Adding a native exclusive child must not switch off the existing choice"
    assert all(background_layers()[key].id() == identity for key, identity in existing.items())
    assert project.readNumEntry("AgTechTooling", "background_catalog_version")[0] == CATALOG_VERSION
    # Re-running and explicit provider overrides retain their native layer/source.
    esri = background_layers()["esri_world"]
    uri.setEncodedUri(esri.source())
    uri.removeParam("url")
    uri.setParam("url", "https://example.invalid/my-imagery/{z}/{x}/{y}.png")
    esri.setDataSource(bytes(uri.encodedUri()).decode(), esri.name(), "wms")
    ensure_background()
    assert "example.invalid" in background_layers()["esri_world"].source()
    # All-off and a hidden group remain off when this new option is added.
    for hidden in (False, True):
        project.removeMapLayer(background_layers()["esri_world"].id())
        group.setItemVisibilityChecked(not hidden)
        for layer in background_layers().values():
            tree.findLayer(layer.id()).setItemVisibilityChecked(False)
        project.writeEntry("AgTechTooling", "background_catalog_version", 1)
        ensure_background()
        assert not any(tree.findLayer(layer.id()).isVisible() for layer in background_layers().values())
        assert group.itemVisibilityChecked() == (not hidden)
    # Esri can be saved/reopened, and deliberate removal stays removed afterwards.
    group.setItemVisibilityChecked(True)
    node("esri_world").setItemVisibilityChecked(True)
    with tempfile.TemporaryDirectory(prefix="agtech-esri-") as temporary:
        filename = str(Path(temporary) / "Map.qgz")
        assert project.write(filename)
        assert project.read(filename)
        ensure_background()
        assert node("esri_world").isVisible()
    project.removeMapLayer(background_layers()["esri_world"].id())
    ensure_background()
    assert "esri_world" not in background_layers()
    # Deleting the whole catalogue is respected across a version upgrade too.
    group = node("osm").parent()
    tree.removeChildNode(group)
    project.writeEntry("AgTechTooling", "background_catalog_version", 1)
    ensure_background()
    assert not any(n.customProperty("AgTechTooling/background_group", False) for n in tree.children())
    print("Esri native catalogue, attribution, settings, v1 upgrades, visibility, deletions, source overrides and save/reopen passed")
finally:
    project.clear()
    app.exitQgis()
