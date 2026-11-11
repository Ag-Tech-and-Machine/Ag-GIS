# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

    # SPDX-License-Identifier: GPL-2.0-or-later

    """Optional exclusive backdrops through the native QGIS WMS provider/cache."""

    from qgis.PyQt.QtCore import QObject, QTimer, QUrl, Qt, QEvent

    from qgis.PyQt.QtGui import QColor, QFont, QFontMetrics

    from html import escape

    from qgis.PyQt.QtWidgets import QLabel, QStyle, QStyleOptionViewItem

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsProject, QgsRasterLayer, QgsLayerTreeLayer, QgsDataSourceUri, QgsHttpHeaders, QgsNetworkAccessManager
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this module

from .view_settings import preference



OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"

USER_AGENT = "Ag-GIS (+https://github.com/JamRov/Ag-GIS)"

CREDIT = "© OpenStreetMap contributors · openstreetmap.org/copyright"





def identify_request(request):

    # QGIS replaces URI User-Agent headers in its network manager. Its native

    # preprocessor runs afterwards, including provider worker-thread requests.

    if request.url().host() == "tile.openstreetmap.org":

        request.setRawHeader(b"User-Agent", USER_AGENT.encode("ascii"))





PROVIDERS = {

    "osm": dict(name="Roads — OpenStreetMap", url=OSM_URL, zmax=19,

                credit=CREDIT, link="https://www.openstreetmap.org/copyright",

                description="Online roads and places. Not satellite imagery."),

    "esri_world": dict(name="Imagery — Esri World Imagery", introduced=2,

                url="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",

                zmax=23,

                credit="Powered by Esri · Source: Esri, Vantor, Earthstar Geographics, and the GIS User Community",

                link="https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9",

                description="Worldwide aerial and satellite imagery. Detail and capture date vary by location; not live or survey-grade. Esri service terms apply; not an open-data licence. Visible tiles are requested from Esri; no bulk/offline imagery download."),

    "satellite_au": dict(name="Satellite — Australia 2025 (30 m)",

                url="https://ows.dea.ga.gov.au/?service=WMTS&request=GetTile&version=1.0.0&layer=ga_ls8cls9c_gm_cyear_3&style=simple_rgb&format=image/png&tilematrixset=WholeWorld_WebMercator&tilematrix={z}&tilerow={y}&tilecol={x}&time=2025-01-01",

                zmax=14, credit="Digital Earth Australia — Geoscience Australia · Landsat 8/9 GeoMAD 2025 · CC BY 4.0",

                link="https://knowledge.dea.ga.gov.au/data/product/dea-geometric-median-and-median-absolute-deviation-landsat/",

                description="Australia only. Annual 2025 cloud-free composite, 30 m pixels. Not current aerial photography."),

    "satellite_world": dict(name="Satellite — World 2016–17 (10 m)",

                url="https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg",

                zmax=14, credit="EOxCloudless https://cloudless.eox.at by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2016 & 2017) · CC BY 4.0",

                link="https://cloudless.eox.at/license-non-commercial",

                description="Worldwide historical Sentinel-2 composite, 10 m pixels, 2016–17 imagery. Not current aerial photography."),

}

CATALOG_VERSION = 2





def background_layers(project=None):

    project = project or QgsProject.instance()

    return {str(layer.customProperty("AgTechTooling/background")): layer

            for layer in project.mapLayers().values()

            if layer.customProperty("AgTechTooling/background") in PROVIDERS}





def _add_layer(project, group, key):

    specification = PROVIDERS[key]

    uri = QgsDataSourceUri()

    uri.setParam("type", "xyz")

    uri.setParam("url", specification["url"])

    uri.setParam("zmin", "0")

    uri.setParam("zmax", str(specification["zmax"]))

    headers = QgsHttpHeaders()

    headers.insert("User-Agent", USER_AGENT)

    uri.setHttpHeaders(headers)

    layer = QgsRasterLayer(bytes(uri.encodedUri()).decode(), specification["name"], "wms")

    if not layer.isValid():

        raise ValueError("Ag-GIS could not prepare " + specification["name"])

    layer.setCustomProperty("AgTechTooling/background", key)

    metadata = layer.metadata()

    metadata.setRights([specification["credit"]])

    metadata.setAbstract(specification["description"] + " Internet required. " + specification["link"])

    layer.setMetadata(metadata)

    project.addMapLayer(layer, False)

    # Insert unchecked, not check-then-uncheck: an initially checked child in a

    # native exclusive group can turn off the user's existing selected map.

    checked = [(child, child.itemVisibilityChecked()) for child in group.children()]

    node = QgsLayerTreeLayer(layer)

    node.setItemVisibilityChecked(False)

    group.addChildNode(node)

    # QGIS may pick a child on insertion even when the group was all-off.

    for child, enabled in checked:

        child.setItemVisibilityChecked(enabled)

    node.setItemVisibilityChecked(False)

    return layer





def ensure_background(project=None, restore=None):

    """Install the checkbox catalogue once; preserve later checkbox/deletion choices."""

    project = project or QgsProject.instance()

    if project.readNumEntry("AgTechTooling", "schema_version")[0] != 2:

        return None

    tree, layers = project.layerTreeRoot(), background_layers(project)

    catalogue = project.readNumEntry("AgTechTooling", "background_catalog_version", 0)[0]

    group = next((n for n in tree.children() if n.customProperty("AgTechTooling/background_group", False)), None)

    if group is None and catalogue >= 1 and restore is None:

        return layers.get("osm")

    if group is None:

        group = tree.addGroup("Background")

        group.setCustomProperty("AgTechTooling/background_group", True)

    first_catalogue = catalogue < 1

    previous = [key for key, layer in layers.items()

                if (node := tree.findLayer(layer.id())) is not None and node.isVisible()]

    deleted_osm = not layers.get("osm") and project.readBoolEntry("AgTechTooling", "background_initialised", False)[0]

    if layers.get("osm") and layers["osm"].name() == "OpenStreetMap":

        layers["osm"].setName(PROVIDERS["osm"]["name"])

    for key, specification in PROVIDERS.items():

        newly_available = catalogue < specification.get("introduced", 1) <= CATALOG_VERSION

        if key not in layers and ((newly_available and not (key == "osm" and deleted_osm)) or restore == key):

            layers[key] = _add_layer(project, group, key)

        elif key in layers and key.startswith("satellite_"):

            # Repair our original catalogue in saved maps as well as new maps.

            # DEA advertises matrices 0–14 only. Requesting 15–17 returns HTTP

            # 400; QGIS must enlarge supported tiles at closer farm scales.

            # Cap the 10 m world composite too, avoiding empty extra detail.

            layer = layers[key]

            uri = QgsDataSourceUri(); uri.setEncodedUri(layer.source())

            if (uri.param("type") == "xyz" and uri.param("url") == PROVIDERS[key]["url"]

                    and uri.param("zmax") == "17"):

                uri.removeParam("zmax")

                uri.setParam("zmax", str(PROVIDERS[key]["zmax"]))

                layer.setDataSource(bytes(uri.encodedUri()).decode(), layer.name(), "wms")

    # On migration, preserve the existing checked map; on first creation use the

    # selected default. A deliberately removed/unchecked map stays that way.

    if first_catalogue:

        group.setIsMutuallyExclusive(True)

        selected = previous[0] if previous else (preference("background", project) if not project.readBoolEntry("AgTechTooling", "background_initialised", False)[0] else "none")

        for key, layer in layers.items():

            node = tree.findLayer(layer.id())

            if node:

                node.setItemVisibilityChecked(key == selected)



        project.writeEntry("AgTechTooling", "view/background", selected)

        project.writeEntry("AgTechTooling", "background_initialised", True)

        group.setExpanded(True)

    elif not group.isMutuallyExclusive():

        group.setIsMutuallyExclusive(True)

    if catalogue < CATALOG_VERSION:

        project.writeEntry("AgTechTooling", "background_catalog_version", CATALOG_VERSION)

    return layers.get("osm")





class BackgroundMaps(QObject):

    def __init__(self, iface):

        super().__init__()

        self.iface, self.closed = iface, False

        self.mutating = False

        self.last_visible = None

        self.visibility_timer = QTimer(self)

        self.visibility_timer.setSingleShot(True)

        self.visibility_timer.timeout.connect(self.sync_visibility)

        self.view = iface.layerTreeView() if hasattr(iface, "layerTreeView") else None

        if self.view is not None:

            self.view.viewport().installEventFilter(self)

        self.processor = QgsNetworkAccessManager.setRequestPreprocessor(identify_request)

        self.canvas = iface.mapCanvas()

        self.label = None

        self.transition = None

        self.rendering_providers = None

        self.completed_providers = None

        self.pending_background = None

        if hasattr(self.canvas, "renderComplete"):

            self.label = QLabel('<a href="https://www.openstreetmap.org/copyright">' + CREDIT + '</a>', self.canvas)

            self.label.setFont(QFont("Sans Serif", 9))

            self.label.setOpenExternalLinks(True)

            self.label.setStyleSheet("background: white; color: #222; padding: 3px;")

            self.label.setToolTip("Online background · OpenStreetMap licence and attribution")

            self.label.adjustSize()

            self.canvas.installEventFilter(self)

            self.canvas.renderComplete.connect(self.render_credit)

            self.transition = QLabel(self.canvas)

            self.transition.setObjectName("ag_tech_tooling_background_transition")

            self.transition.setTextFormat(Qt.PlainText)

            self.transition.setAlignment(Qt.AlignCenter)

            self.transition.setWordWrap(True)

            self.transition.setAttribute(Qt.WA_TransparentForMouseEvents)

            self.transition.setStyleSheet("background: white; color: #222; padding: 20px;")

            self.transition.hide()

            self.canvas.renderStarting.connect(self.render_started)

            self.canvas.mapCanvasRefreshed.connect(self.render_finished)

        project = QgsProject.instance()

        project.readProject.connect(self.schedule)

        project.cleared.connect(self.schedule)

        project.layersRemoved.connect(self.schedule)

        project.layerTreeRoot().visibilityChanged.connect(self.visibility_changed)

        self.schedule()



    def schedule(self, *args):

        QTimer.singleShot(0, self.refresh)



    def refresh(self):

        if self.closed:

            return

        self.mutating = True

        try:

            ensure_background()

        finally:

            self.mutating = False

        self.sync_visibility()



    def visible_providers(self):

        project = QgsProject.instance()

        return [key for key, layer in background_layers(project).items()

                if (node := project.layerTreeRoot().findLayer(layer.id())) is not None and node.isVisible()]



    def visible(self):

        return bool(self.visible_providers())



    def visibility_changed(self, *args):

        if self.closed or self.mutating:

            return

        node = args[0] if args else None

        if node is not None and not (node.customProperty("AgTechTooling/background_group", False)

                or (hasattr(node, "layer") and node.layer()

                    and node.layer().customProperty("AgTechTooling/background") in PROVIDERS)):

            return

        # Native exclusive groups emit intermediate off/on signals. Read their

        # final state after the native canvas bridge has updated its layer list.

        self.visibility_timer.start(0)



    def sync_visibility(self):

        if self.closed:

            return

        project = QgsProject.instance()

        visible = self.visible_providers()

        if project.readNumEntry("AgTechTooling", "schema_version")[0] == 2:

            selected = visible[0] if visible else "none"

            if preference("background", project) != selected:

                project.writeEntry("AgTechTooling", "view/background", selected)

        self.update_credit()

        if visible != self.last_visible and hasattr(self.canvas, "refresh"):

            self.show_transition(visible)

            if hasattr(self.canvas, "stopRendering"):

                self.canvas.stopRendering()

            self.canvas.refresh()

        self.last_visible = visible



    def canvas_providers(self):

        return [key for layer in self.canvas.layers()

                if (key := layer.customProperty("AgTechTooling/background")) in PROVIDERS]



    def show_transition(self, selected):

        if self.transition is None:

            return

        self.pending_background = list(selected)

        name = PROVIDERS[selected[0]]["name"] if selected else "Off"

        message = "Changing background…\n" + name

        if not self.canvas.renderFlag():

            message += "\nMap drawing is paused. Turn on Render to update the map."

        self.transition.setText(message)

        self.transition.setGeometry(self.canvas.rect())

        self.transition.show()

        self.transition.raise_()

        self.label.hide()



    def render_started(self):

        self.rendering_providers = self.canvas_providers()

        self.completed_providers = None



    def render_finished(self):

        # Native QGIS emits mapCanvasRefreshed for cancelled jobs too. Only a

        # completed render matching the *latest* tree choice may uncover the map.

        if self.closed:

            return

        if (self.pending_background is not None

                and self.completed_providers == self.pending_background

                and self.visible_providers() == self.pending_background

                and self.canvas_providers() == self.pending_background):

            self.pending_background = None

            self.transition.hide()

            self.update_credit()

        self.rendering_providers = None



    def choose(self, key):

        if self.closed or key not in {*PROVIDERS, "none"}:

            return

        project = QgsProject.instance()

        self.mutating = True

        try:

            ensure_background(project, restore=key)

            for identifier, layer in background_layers(project).items():

                node = project.layerTreeRoot().findLayer(layer.id())

                if node:

                    node.setItemVisibilityChecked(identifier == key)

                    if identifier == key:

                        node.setItemVisibilityCheckedParentRecursive(True)

            project.writeEntry("AgTechTooling", "view/background", key)

        finally:

            self.mutating = False

        self.visibility_timer.start(0)



    def credit_text(self):

        return " · ".join(PROVIDERS[key]["credit"] for key in self.visible_providers())



    def update_credit(self, *args):

        if self.closed or self.label is None:

            return

        selected = self.visible_providers()

        self.label.setToolTip("\n".join(PROVIDERS[key]["description"] for key in selected))

        text = ' · '.join('<a href="' + PROVIDERS[key]["link"] + '">' + escape(PROVIDERS[key]["credit"]) + '</a>' for key in selected)

        self.label.setText(text)

        self.label.setWordWrap(True)

        width = QFontMetrics(self.label.font()).horizontalAdvance(self.credit_text()) + 12

        self.label.setFixedWidth(min(width, max(100, self.canvas.width() - 8)))

        self.label.adjustSize()

        self.label.move(max(0, self.canvas.width() - self.label.width() - 4),

                        max(0, self.canvas.height() - self.label.height() - 4))

        self.label.setVisible(self.visible() and self.pending_background is None)

        self.label.raise_()

        if self.pending_background is not None:

            self.transition.setGeometry(self.canvas.rect())

            self.transition.raise_()



    def eventFilter(self, watched, event):

        if self.view is not None and watched is self.view.viewport() and event.type() == QEvent.MouseButtonRelease:

            if event.button() == Qt.LeftButton and event.modifiers() == Qt.NoModifier:

                index = self.view.indexAt(event.pos())

                node = self.view.index2node(index)

                layer = node.layer() if node is not None and hasattr(node, "layer") else None

                key = layer.customProperty("AgTechTooling/background") if layer else None

                if key in PROVIDERS:

                    option = QStyleOptionViewItem()

                    self.view.itemDelegate().initStyleOption(option, index)

                    option.rect = self.view.visualRect(index); option.widget = self.view

                    checkbox = self.view.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator, option, self.view)

                    if not checkbox.contains(event.pos()):

                        # A name click selects a backdrop; a checkbox click keeps

                        # native QGIS toggle/off behaviour, including keyboard use.

                        QTimer.singleShot(0, lambda selected=key: self.choose(selected))

        if event.type() == QEvent.Resize:

            self.update_credit()

        return False



    def render_credit(self, painter):

        # Native canvas image exports also receive attribution; print layouts use

        # the layer's rights metadata and must include their own attribution item.

        if self.closed:

            return

        selected = self.rendering_providers if self.rendering_providers is not None else self.visible_providers()

        if self.rendering_providers is not None:

            self.completed_providers = list(self.rendering_providers)

        if not selected:

            return

        painter.save()

        painter.setFont(QFont("Sans Serif", 9))

        rect = painter.viewport().adjusted(6, 6, -6, -6)

        painter.setPen(QColor("#222222"))

        painter.setBackground(QColor("white"))

        painter.setBackgroundMode(Qt.OpaqueMode)

        painter.drawText(rect, Qt.AlignBottom | Qt.AlignRight | Qt.TextWordWrap,

                         " · ".join(PROVIDERS[key]["credit"] for key in selected))

        painter.restore()



    def close(self):

        self.closed = True

        self.visibility_timer.stop()

        if self.view is not None:

            self.view.viewport().removeEventFilter(self)

        QgsNetworkAccessManager.removeRequestPreprocessor(self.processor)

        project = QgsProject.instance()

        project.readProject.disconnect(self.schedule)

        project.cleared.disconnect(self.schedule)

        project.layersRemoved.disconnect(self.schedule)

        project.layerTreeRoot().visibilityChanged.disconnect(self.visibility_changed)

        if self.label is not None:

            self.canvas.renderComplete.disconnect(self.render_credit)

            self.canvas.renderStarting.disconnect(self.render_started)

            self.canvas.mapCanvasRefreshed.disconnect(self.render_finished)

            self.canvas.removeEventFilter(self)

            self.label.hide()

            self.label.deleteLater()

            self.transition.hide()

            self.transition.deleteLater()


