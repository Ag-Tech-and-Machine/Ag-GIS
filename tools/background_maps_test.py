# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

    """Native checkbox switching, saved choice, migration, removal and attribution."""

    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from pathlib import Path

    import sys, tempfile

    from contextlib import ExitStack

    sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1]/"plugins")))

    from qgis.PyQt.QtCore import Qt, QSettings

    from qgis.PyQt.QtWidgets import QMainWindow, QDockWidget, QStyle, QStyleOptionViewItem

    from qgis.PyQt.QtTest import QTest

    from qgis.core import QgsApplication, QgsProject, QgsLayerTreeModel

    from qgis.gui import QgsMapCanvas, QgsLayerTreeView, QgsLayerTreeMapCanvasBridge

    from unittest.mock import patch

    from ag_tech_tooling.workspace_defaults import create_default

    from ag_tech_tooling import view_settings

    from ag_tech_tooling.background_maps import ensure_background, background_layers, BackgroundMaps, PROVIDERS

    from ag_tech_tooling.farm_browser import FarmBrowser

    

    app=QgsApplication([],False);app.initQgis();project=QgsProject.instance()

    with tempfile.TemporaryDirectory(prefix="agtech-backgrounds-") as temporary, ExitStack() as cleanup:

        cleanup.callback(project.clear)

        settings=QSettings(str(Path(temporary)/"settings.ini"),QSettings.IniFormat)

        with patch.object(view_settings,"QgsSettings",return_value=settings):

            root=create_default(parent=temporary)

            assert project.read(str(root/"Farm.qgz"))

            layers=background_layers();assert set(layers)==set(PROVIDERS)

            group=project.layerTreeRoot().children()[-1]

            assert group.isMutuallyExclusive() and group.isExpanded()

            assert all(layer.isValid() and "key=" not in layer.source() for layer in layers.values())

            assert len(project.mapLayers())==3+len(PROVIDERS)

            class Interface:

                def __init__(self):

                    self.window=QMainWindow();self.canvas=QgsMapCanvas();self.window.setCentralWidget(self.canvas)

                    self.canvas.setRenderFlag(False)  # Interaction checks never request public tiles.

                    self.view=QgsLayerTreeView();self.model=QgsLayerTreeModel(project.layerTreeRoot())

                    self.model.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility,True);self.view.setModel(self.model)

                    self.dock=QDockWidget("Layers",self.window);self.dock.setWidget(self.view)

                    self.window.addDockWidget(Qt.LeftDockWidgetArea,self.dock);self.window.resize(1200,800)

                    self.bridge=QgsLayerTreeMapCanvasBridge(project.layerTreeRoot(),self.canvas)

                def layerTreeView(self):return self.view

                def mainWindow(self):return self.window

                def mapCanvas(self):return self.canvas

            iface=Interface();browser=FarmBrowser(iface);iface.window.show();controller=BackgroundMaps(iface);app.processEvents()

            assert controller.visible_providers()==["osm"]

            def click(key, label=False):

                node=project.layerTreeRoot().findLayer(layers[key].id());index=iface.view.node2index(node)

                iface.view.scrollTo(index);app.processEvents()

                option=QStyleOptionViewItem();iface.view.itemDelegate().initStyleOption(option,index)

                option.rect=iface.view.visualRect(index);option.widget=iface.view

                rect=iface.view.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator,option,iface.view)

                position=option.rect.center() if label else rect.center()

                QTest.mouseClick(iface.view.viewport(),Qt.LeftButton,Qt.NoModifier,position);QTest.qWait(20)

            for key in ("satellite_world","satellite_au","esri_world","osm")*3:

                click(key)

                assert controller.visible_providers()==[key],controller.visible_providers()

                assert view_settings.preference("background")==key

                assert [l for l in iface.canvas.layers() if l.customProperty("AgTechTooling/background")]==[layers[key]]

                assert PROVIDERS[key]["credit"] in controller.credit_text()

                assert PROVIDERS[key]["description"]==controller.label.toolTip()

                if key == "satellite_world":

                    assert controller.label.width() > 500, "Long attribution should use available width rather than a narrow column"

            click("osm");assert not controller.visible_providers()

            click("osm",label=True);assert controller.visible_providers()==["osm"]

            click("satellite_world",label=True);assert controller.visible_providers()==["satellite_world"]

            click("satellite_world");assert not controller.visible_providers(), "A checkbox must still switch the chosen map off"

            group.setItemVisibilityChecked(False);controller.choose("satellite_au");QTest.qWait(20)

            assert controller.visible_providers()==["satellite_au"], "Settings must re-enable a hidden group"

            controller.choose("none");QTest.qWait(20);assert not controller.visible_providers()

            click("satellite_au");assert controller.visible_providers()==["satellite_au"]

            assert project.write()

            project.clear();QTest.qWait(20)

            assert project.read(str(root/"Farm.qgz"));QTest.qWait(20);ensure_background()

            layers=background_layers()

            checked=[key for key,layer in layers.items() if project.layerTreeRoot().findLayer(layer.id()).isVisible()]

            assert checked==["satellite_au"] and view_settings.preference("background")=="satellite_au"

            assert [l for l in iface.canvas.layers() if l.customProperty("AgTechTooling/background")]==[layers["satellite_au"]]

            browser.close();controller.close();iface.window.close()

            # Existing saved catalogue from 0.12.0/1 used invalid DEA matrix levels.

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
                from qgis.core import QgsDataSourceUri
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this test

        au=layers["satellite_au"];old=QgsDataSourceUri();old.setEncodedUri(au.source());old.removeParam("zmax");old.setParam("zmax","17")

        au.setDataSource(bytes(old.encodedUri()).decode(),au.name(),"wms")

        identity=au.id();ensure_background();fixed=QgsDataSourceUri();fixed.setEncodedUri(au.source())

        assert au.id()==identity and fixed.param("zmax")=="14" and au.isValid()

        assert project.layerTreeRoot().findLayer(identity).isVisible()

        custom_url="https://example.invalid/custom/{z}/{x}/{y}.png"

        old.removeParam("url");old.setParam("url",custom_url);au.setDataSource(bytes(old.encodedUri()).decode(),au.name(),"wms")

        ensure_background();custom=QgsDataSourceUri();custom.setEncodedUri(au.source())

        assert custom.param("url")==custom_url and custom.param("zmax")=="17", "Preserve user-edited sources"

        # Migration from the old single-background layout preserves an unchecked

        # OSM choice, adds the new options unchecked, and exposes the checkboxes.

        project.removeEntry("AgTechTooling","background_catalog_version")

        for key in ("satellite_au","satellite_world"):project.removeMapLayer(layers[key].id())

        osm=project.layerTreeRoot().findLayer(layers["osm"].id());osm.setItemVisibilityChecked(False)

        ensure_background();layers=background_layers();assert set(layers)==set(PROVIDERS)

        assert not any(project.layerTreeRoot().findLayer(l.id()).isVisible() for l in layers.values())

        # Manual removal is remembered, while an explicit settings selection can restore it.

        project.removeMapLayer(layers["satellite_world"].id());ensure_background()

        assert "satellite_world" not in background_layers()

        ensure_background(restore="satellite_world");assert "satellite_world" in background_layers()

        dialog=view_settings.ViewSettingsDialog();assert dialog.background.count()==len(PROVIDERS)+1;dialog.reject()

        project.clear()

print("Background native checkboxes, exclusive selection, attribution, save/reopen, migration and removal passed")

app.exitQgis()


