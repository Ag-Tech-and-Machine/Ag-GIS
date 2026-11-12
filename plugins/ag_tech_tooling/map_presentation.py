# SPDX-License-Identifier: GPL-2.0-or-later
"""Readable starting names/symbols and native coordinate-aware canvas zoom."""
import re
from qgis.core import (QgsProject, QgsVectorLayer, QgsWkbTypes, QgsSingleSymbolRenderer,
    QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol, QgsMapLayerStyle, QgsRectangle, QgsFeatureRenderer,
    QgsCoordinateTransform)
from .view_settings import preference


def friendly_name(name):
    name = re.sub(r"[_\s]+", " ", name).strip()
    name = re.sub(r"\s+\d{4}-\d{2}-\d{2}(?:[ T_-]\d{2}(?:[ :_-]\d{2})*)?(?:\s+\d+)?$", "", name)
    return name if len(name) <= 48 else name[:45].rstrip() + "…"


def rename_dataset(root, identity, name):
    from . import hierarchy as store
    from .managed_data import TABLE, records
    name = store.text(name)
    if identity not in {row["id"] for row in records(root)}:
        raise ValueError("The saved dataset could not be found.")
    catalogue = QgsVectorLayer(store.layer_uri(root, TABLE), "Dataset names", "ogr")
    feature = next((f for f in catalogue.getFeatures() if f["id"] == identity), None)
    if feature is None or not catalogue.dataProvider().changeAttributeValues({feature.id(): {catalogue.fields().indexFromName("name"): name}}):
        raise ValueError("Ag-GIS could not save the dataset name.")


def prepare_layer(layer, project=None):
    """Apply once to plain owned data. Retain thematic and shaped custom symbols."""
    project = project or QgsProject.instance()
    if not layer.customProperty("AgTechTooling/workspace"):
        return
    if layer.customProperty("AgTechTooling/import_field") and not layer.customProperty("AgTechTooling/name_initialised", False):
        if preference("labels", project):
            layer.setCustomProperty("AgTechTooling/original_name", layer.name())
            layer.setName(friendly_name(layer.name()))
        layer.setCustomProperty("AgTechTooling/name_initialised", True)
    if not isinstance(layer, QgsVectorLayer) or layer.customProperty("AgTechTooling/style_initialised", False):
        return
    if not preference("styling", project):
        return
    renderer = layer.renderer()
    if not isinstance(renderer, QgsSingleSymbolRenderer):
        return
    symbol = renderer.symbol()
    native_renderer = QgsFeatureRenderer.defaultRenderer(layer.geometryType())
    if native_renderer is None:
        return
    native = native_renderer.symbol()
    if symbol.symbolLayerCount() != 1 or symbol.dataDefinedProperties().hasActiveProperties():
        return
    properties = symbol.symbolLayer(0).properties()
    defaults = native.symbolLayer(0).properties()
    if any(value != defaults.get(key) for key, value in properties.items() if key not in {"color", "line_color"}):
        return
    # QGIS default single symbols may be adjusted once; users' later edits win.
    before = QgsMapLayerStyle()
    before.readFromLayer(layer)
    role = layer.customProperty("AgTechTooling/import_role", "")
    table = layer.customProperty("AgTechTooling/table", "")
    boundary = role == "boundary" or table == "agtech_boundaries"
    if layer.geometryType() == QgsWkbTypes.PointGeometry:
        # Keep a lone location at QGIS's readable native size. The compact
        # multi-point theme is useful for dense datasets, but shrinks one marker
        # to about three pixels at 96 dpi; coordinate zoom cannot enlarge it.
        size = "2" if layer.featureCount() == 1 else "0.65"
        symbol = QgsMarkerSymbol.createSimple(dict(name="circle", color="35,131,72,180", size=size, outline_style="no"))
    elif layer.geometryType() == QgsWkbTypes.LineGeometry:
        symbol = QgsLineSymbol.createSimple(dict(line_color="39,123,72,220", line_width="0.45"))
    elif layer.geometryType() == QgsWkbTypes.PolygonGeometry:
        symbol = QgsFillSymbol.createSimple(dict(color="61,150,90,45", style="no" if boundary else "solid",
                                                 outline_color="30,105,60,255", outline_width="0.5"))
    else:
        return
    layer.setCustomProperty("AgTechTooling/starting_style_backup", before.xmlData())
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.setCustomProperty("AgTechTooling/style_initialised", True)
    layer.triggerRepaint()


def zoom_layers(iface, layers):
    canvas = iface.mapCanvas()
    if not hasattr(canvas, "mapSettings"):
        return False
    project, extent = QgsProject.instance(), QgsRectangle()
    extent.setMinimal()
    found = False
    for layer in layers:
        if not layer.isValid() or not layer.isSpatial() or not layer.crs().isValid():
            continue
        if isinstance(layer, QgsVectorLayer):
            layer.updateExtents()
            if layer.featureCount() == 0:
                continue
        rectangle = layer.extent()
        if rectangle.isNull() and rectangle.isEmpty():
            # A single point still has a useful location.
            if not isinstance(layer, QgsVectorLayer) or layer.featureCount() != 1:
                continue
        try:
            rectangle = QgsCoordinateTransform(layer.crs(), canvas.mapSettings().destinationCrs(), project).transformBoundingBox(rectangle)
            extent.combineExtentWith(rectangle)
            found = True
        except Exception:
            continue
    if not found:
        return False
    if extent.width() == 0 or extent.height() == 0:
        margin = 0.001 if canvas.mapSettings().destinationCrs().isGeographic() else 50
        extent.grow(margin)
    extent.scale(1.12)
    canvas.setExtent(extent)
    canvas.refresh()
    return True
