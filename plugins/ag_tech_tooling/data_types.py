# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:

    # SPDX-License-Identifier: GPL-2.0-or-later

    """Implemented reference-data roles; geometry constrains, but never proves meaning."""

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsVectorLayer, QgsWkbTypes
except ImportError:
    pass  # QGIS not available, skip this import

except ImportError:

    pass  # QGIS not available, skip this module



TYPES = {

    "data": ("Other data", "whole", {"point", "line", "polygon", "table", "unknown", "raster"}),

    "boundary": ("Field boundaries", "field", {"polygon"}),

    "guidance": ("Guidance lines", "guidance", {"line"}),

    "assets": ("Infrastructure", "asset", {"point", "line", "polygon"}),

    "samples": ("Sample points", "asset", {"point"}),

    "zones": ("Management zones", "field", {"polygon", "raster"}),

    "elevation": ("Elevation / terrain", "terrain", {"raster"}),

    "imagery": ("Aerial imagery", "terrain", {"raster"}),

    "vegetation": ("Vegetation index", "terrain", {"raster"}),

}





def representation(layer):

    if not isinstance(layer, QgsVectorLayer):

        return "raster"

    return {QgsWkbTypes.PointGeometry: "point", QgsWkbTypes.LineGeometry: "line",

            QgsWkbTypes.PolygonGeometry: "polygon", QgsWkbTypes.NullGeometry: "table"}.get(layer.geometryType(), "unknown")





def allowed(kind):

    return [key for key, (_, _, kinds) in TYPES.items() if kind in kinds]





def validate(layer, role):

    if role not in TYPES or representation(layer) not in TYPES[role][2]:

        raise ValueError("Choose a data type compatible with this layer.")


