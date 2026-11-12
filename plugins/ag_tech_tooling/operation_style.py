# SPDX-License-Identifier: GPL-2.0-or-later
"""Opt-in native vector styles for homogeneous operation datasets.

Not wired into import yet. Does not reinterpret feature values, raster bands,
reference roles or latest field activity. Native renderer edits remain editable.
"""
import json
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsVectorLayer, QgsSymbol, QgsSingleSymbolRenderer, QgsMapLayerStyle
from .classification import VERSION

CLASSIFICATION_KEY = "AgTechTooling/classification_v1"
STYLE_KEY = "AgTechTooling/operation_style_initialised"
COLOURS = {"tillage": "#a6763e", "planting": "#2e8b57", "spraying": "#2878b5",
           "spreading": "#9b59b6", "harvesting": "#d99b19", "unknown": "#777777"}


def apply_operation_style(layer, *, reset=False):
    """Apply once, or explicitly reset; caller owns review and project saving.

Only a versioned explicit operation classification on an owned vector qualifies.
The original native style is retained in the project before the first application.
No source provider/schema/geometry/attribute mutation takes place.
"""
    if not isinstance(layer, QgsVectorLayer) or not layer.customProperty("AgTechTooling/workspace"):
        return False
    try:
        record = json.loads(layer.customProperty(CLASSIFICATION_KEY, "{}"))
    except (ValueError, TypeError):
        return False
    if not isinstance(record, dict) or record.get("version") != VERSION or record.get("purpose") != "operation":
        return False
    if layer.customProperty(STYLE_KEY, False) and not reset:
        return False
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    if symbol is None:
        return False
    operation = record.get("operation_subtype", "unknown")
    if not isinstance(operation, str):
        return False
    symbol.setColor(QColor(COLOURS.get(operation, COLOURS["unknown"])))
    if not layer.customProperty(STYLE_KEY, False):
        before = QgsMapLayerStyle()
        before.readFromLayer(layer)
        layer.setCustomProperty("AgTechTooling/operation_style_backup", before.xmlData())
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.setCustomProperty(STYLE_KEY, True)
    layer.triggerRepaint()
    return True
