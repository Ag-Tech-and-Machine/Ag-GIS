"""Native integration of defaults, overrides, browser actions and safe map presentation."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1] / "plugins")))
from qgis.PyQt.QtCore import Qt, QSettings, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtWidgets import QMainWindow, QDockWidget, QWidget, QVBoxLayout, QToolBar, QDialog, QLineEdit, QMessageBox
from qgis.PyQt.QtTest import QTest
from qgis.core import (QgsApplication, QgsProject, QgsLayerTreeModel, QgsVectorLayer,
    QgsFeature, QgsGeometry, QgsCoordinateReferenceSystem, QgsDataSourceUri,
    QgsSingleSymbolRenderer, QgsMarkerSymbol, QgsNetworkAccessManager)
from qgis.gui import QgsLayerTreeView, QgsMapCanvas
from ag_tech_tooling import hierarchy as store, view_settings
from ag_tech_tooling.workspace_defaults import create_default
from ag_tech_tooling.hierarchy_dialog import sync_tree, NameDialog
from ag_tech_tooling.farm_browser import FarmBrowser
from ag_tech_tooling.background_maps import ensure_background, BackgroundMaps, USER_AGENT, PROVIDERS
from ag_tech_tooling.map_presentation import prepare_layer, zoom_layers

app = QgsApplication([], False)
app.initQgis()
project = QgsProject.instance()
with tempfile.TemporaryDirectory(prefix="agtech-farmer-view-") as temporary, ExitStack() as cleanup:
    cleanup.callback(project.clear)
    settings = QSettings(str(Path(temporary)/"preferences.ini"), QSettings.IniFormat)
    with patch.object(view_settings, "QgsSettings", return_value=settings):
        root = create_default(parent=temporary)
        assert project.read(str(root/"Farm.qgz"))
        assert all(view_settings.preference(k) for k in ("focus", "zoom", "labels", "styling"))
        background = ensure_background()
        assert background and background.isValid()
        uri = QgsDataSourceUri(); uri.setEncodedUri(background.source())
        assert uri.httpHeaders()["User-Agent"] == USER_AGENT, uri.httpHeaders().headers()
        assert len([l for l in project.mapLayers().values() if l.customProperty("AgTechTooling/background")]) == len(PROVIDERS)
        background_node = project.layerTreeRoot().findLayer(background.id())
        assert project.layerTreeRoot().children()[-1].customProperty("AgTechTooling/background_group"), "Keep the backdrop below farm data"
        background_node.setItemVisibilityChecked(False)
        ensure_background()
        assert not background_node.itemVisibilityChecked(), "Respect manual background override"
        rows = store.records(root)
        second = store.add_record(root, "field", "Second", rows["farm"][0]["id"])
        _, nodes = sync_tree(root)
        first = rows["field"][0]["id"]
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "A_very_long_file_name_from_the_machine_with_many_words_2025-02-02_00", "memory")
        feature = QgsFeature(); feature.setGeometry(QgsGeometry.fromWkt("POINT(145 -36)"))
        layer.dataProvider().addFeatures([feature]); layer.updateExtents()
        from ag_tech_tooling.import_placement import place_layer
        place_layer(root, layer, first)
        assert len(layer.name()) <= 48 and "_" not in layer.name()
        assert layer.customProperty("AgTechTooling/original_name").endswith("2025-02-02_00")
        # A lone imported location must remain discoverable at native 96 dpi.
        # Zoom cannot enlarge millimetre-sized markers; inspect actual rendered pixels.
        from qgis.core import QgsMapSettings, QgsMapRendererSequentialJob, QgsRectangle
        from qgis.PyQt.QtCore import QSize
        from qgis.PyQt.QtGui import QColor
        render = QgsMapSettings()
        render.setLayers([layer]); render.setDestinationCrs(layer.crs())
        render.setExtent(QgsRectangle(144.99, -36.01, 145.01, -35.99))
        render.setOutputSize(QSize(400, 400)); render.setOutputDpi(96)
        render.setBackgroundColor(QColor('white'))
        job = QgsMapRendererSequentialJob(render); job.start(); job.waitForFinished()
        image = job.renderedImage()
        marked = [(x, y) for y in range(image.height()) for x in range(image.width())
                  if image.pixelColor(x, y).green() - image.pixelColor(x, y).red() > 20]
        diameter = max(x for x, y in marked) - min(x for x, y in marked) + 1 if marked else 0
        print('Single-point native rendered diameter:', diameter, 'pixels; marker size:',
              layer.renderer().symbol().size(), 'unit:', layer.renderer().symbol().sizeUnit(), flush=True)
        assert diameter >= 6, 'A lone location is rendered as a near-invisible dot'
        assert layer.renderer().symbol().size() == 2
        # Preserve deliberately tiny/source-authored markers, initialized saved styles,
        # styling opt-out and the existing compact multi-point presentation.
        for label, size, initialised, enabled in (
                ('Source-authored tiny', .65, False, True),
                ('Saved tiny', .65, True, True),
                ('Styling disabled', 2, False, False)):
            protected = QgsVectorLayer('Point?crs=EPSG:4326', label, 'memory')
            protected.dataProvider().addFeatures([feature]); protected.updateExtents()
            protected.setCustomProperty('AgTechTooling/workspace', store.workspace_id(root))
            protected.setCustomProperty('AgTechTooling/style_initialised', initialised)
            protected.renderer().symbol().setSize(size)
            original = protected.renderer().dump()
            project.writeEntry('AgTechTooling', 'view/styling', enabled)
            prepare_layer(protected)
            assert protected.renderer().dump() == original
            assert protected.renderer().symbol().size() == size, label
        project.writeEntry('AgTechTooling', 'view/styling', True)
        dense = QgsVectorLayer('Point?crs=EPSG:4326', 'Two locations', 'memory')
        dense.dataProvider().addFeatures([feature, feature]); dense.updateExtents()
        dense.setCustomProperty('AgTechTooling/workspace', store.workspace_id(root))
        prepare_layer(dense)
        assert dense.renderer().symbol().size() == .65
        from qgis.core import QgsMapLayerStyle
        original_style = QgsMapLayerStyle(layer.customProperty('AgTechTooling/starting_style_backup'))
        backup_layer = QgsVectorLayer('Point?crs=EPSG:4326', 'Original native style', 'memory')
        original_style.writeToLayer(backup_layer)
        assert backup_layer.renderer().symbol().size() == 2
        protected = dense = backup_layer = None
        layer.setName("My sample")
        layer.renderer().symbol().setSize(1.1)
        prepare_layer(layer)
        assert layer.name() == "My sample" and layer.renderer().symbol().size() == 1.1
        custom = QgsVectorLayer("Point?crs=EPSG:4326", "Custom", "memory")
        custom.setCustomProperty("AgTechTooling/workspace", store.workspace_id(root))
        custom.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(dict(name="star", size="4"))))
        prepare_layer(custom)
        assert custom.renderer().symbol().size() == 4

        class Interface:
            def __init__(self):
                self.window = QMainWindow()
                self.canvas = QgsMapCanvas()
                self.canvas.setRenderFlag(False)  # UI checks never download public tiles.
                self.canvas.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
                self.window.setCentralWidget(self.canvas)
                self.view = QgsLayerTreeView()
                self.model = QgsLayerTreeModel(project.layerTreeRoot())
                self.model.setFlag(QgsLayerTreeModel.AllowNodeRename, True)
                self.view.setModel(self.model)
                dock = QDockWidget("Layers", self.window)
                contents = QWidget(); layout = QVBoxLayout(contents)
                self.toolbar = QToolBar(); layout.addWidget(self.toolbar); layout.addWidget(self.view)
                dock.setWidget(contents); self.window.addDockWidget(Qt.LeftDockWidgetArea,dock)
                self.messages=[]
            def layerTreeView(self): return self.view
            def mapCanvas(self): return self.canvas
            def mainWindow(self): return self.window
            def setActiveLayer(self, layer): self.active = layer
            def messageBar(self): return self
            def pushMessage(self,*args,**kwargs): self.messages.append(args)

        iface = Interface(); browser = FarmBrowser(iface)
        iface.window.show(); app.processEvents()
        backgrounds = BackgroundMaps(iface); app.processEvents()
        request = QNetworkRequest(QUrl("https://tile.openstreetmap.org/0/0/0.png"))
        request.setRawHeader(b"User-Agent", b"QGIS")
        manager = QgsNetworkAccessManager.instance()
        manager.preprocessRequest(request)
        assert bytes(request.rawHeader(b"User-Agent")).decode() == USER_AGENT
        unrelated = QNetworkRequest(QUrl("https://example.org/map"))
        unrelated.setRawHeader(b"User-Agent", b"Other client")
        manager.preprocessRequest(unrelated)
        assert bytes(unrelated.rawHeader(b"User-Agent")) == b"Other client"
        background_node.setItemVisibilityChecked(True); app.processEvents()
        assert backgrounds.transition.isVisible() and "paused" in backgrounds.transition.text()
        assert not backgrounds.label.isVisible(), "Do not attach the requested credit to an old, unrendered canvas"
        assert "OpenStreetMap" in backgrounds.credit_text()
        assert zoom_layers(iface,[layer]), "Single-point data must zoom in transformed canvas CRS"
        assert iface.canvas.extent().contains(16141326, -4300621)
        iface.view.setCurrentNode(nodes[first]); app.processEvents()
        assert nodes[first].isExpanded(), "Selected field reveals its choices"
        # Preserve the sibling's existing state, whether manually open or closed.
        nodes[second].setExpanded(True)
        browser.focus_node(nodes[first])
        assert nodes[second].isExpanded(), "Keep comparison fields open"
        nodes[second].setExpanded(False)
        browser.refresh_presentation(); app.processEvents()
        assert not nodes[second].isExpanded(), "Refresh preserves manual collapse"
        iface.view.setCurrentNode(project.layerTreeRoot().findLayer(layer.id())); app.processEvents()
        assert iface.active is layer
        from types import SimpleNamespace
        from ag_tech_tooling.plugin import AgTechTooling
        AgTechTooling.whole_map(SimpleNamespace(iface=iface))
        assert iface.canvas.extent().width() < 1000, "Whole Map must exclude the global background extent"
        assert browser.add_actions["season"].isEnabled()
        assert all(not button.icon().isNull() for _,_,button in browser.buttons)

        iface.view.setCurrentNode(nodes[first]); app.processEvents()
        iface.view.edit(iface.view.node2index(nodes[first])); app.processEvents()
        editor = iface.view.findChild(QLineEdit); assert editor
        editor.setText("  Home Field  "); QTest.keyClick(editor,Qt.Key_Return); app.processEvents()
        assert next(r for r in store.records(root)["field"] if r["id"] == first)["name"] == "Home Field"
        assert nodes[first].name() == "Home Field"
        from ag_tech_tooling.managed_data import save_dataset, records
        from ag_tech_tooling.map_presentation import rename_dataset
        record, saved, created = save_dataset(root, layer, first, "data")
        rename_dataset(root, record["id"], "Soil samples")
        assert next(r for r in records(root) if r["id"] == record["id"])["name"] == "Soil samples"
        saved = None
        class AcceptedName(NameDialog):
            def exec(self): self.name.setText("2027"); return QDialog.Accepted
        with patch("ag_tech_tooling.hierarchy_dialog.NameDialog", AcceptedName): browser.add_entity("season")
        assert any(r["name"] == "2027" for r in store.records(root)["season"])
        before = store.records(root)
        with patch.object(NameDialog,"exec",return_value=QDialog.Rejected): browser.add_entity("crop")
        assert store.records(root) == before
        project.writeEntry("AgTechTooling","view/focus",False)
        nodes[second].setExpanded(True); browser.focus_node(nodes[first]); assert nodes[second].isExpanded()

        dialog = view_settings.ViewSettingsDialog()
        dialog.background.setCurrentIndex(dialog.background.findData("none"))
        dialog.controls["zoom"].setChecked(False); dialog.future.setChecked(True); dialog.accept()
        assert not view_settings.preference("zoom")
        backgrounds.choose("none"); assert not background_node.itemVisibilityChecked()
        future = QgsProject(); view_settings.initialise(future)
        assert view_settings.preference("background",future) == "none"
        assert not view_settings.preference("zoom",future)
        cancelled = view_settings.ViewSettingsDialog(); cancelled.controls["zoom"].setChecked(True); cancelled.reject()
        assert not view_settings.preference("zoom")
        backgrounds.close(); browser.close(); app.processEvents()
        request.setRawHeader(b"User-Agent", b"QGIS")
        manager.preprocessRequest(request)
        assert bytes(request.rawHeader(b"User-Agent")) == b"QGIS", "Remove the native request hook on unload"
        assert not iface.toolbar.actions(), "Browser controls must be removed on unload"
        assert project.write()
        iface.window.close(); iface.canvas.setLayers([]); project.clear(); future.clear()
        assert project.read(str(root/"Farm.qgz"))
        assert view_settings.preference("background") == "none" and not view_settings.preference("zoom")
        restored = next(l for l in project.mapLayers().values() if l.name() == "My sample")
        assert restored.renderer().symbol().size() == 1.1
        project.clear()
        del feature, layer, custom, background
print("Farmer defaults, overrides, names/styles, coordinate zoom, hierarchy add/rename, background attribution and unload passed")
app.exitQgis()
