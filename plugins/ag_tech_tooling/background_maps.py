# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

try:
    # SPDX-License-Identifier: GPL-2.0-or-later

    """Optional exclusive backdrops through the native QGIS WMS provider/cache."""

    from qgis.PyQt.QtCore import QObject, QTimer, QUrl, Qt, QEvent

    from qgis.PyQt.QtGui import QColor, QFont, QFontMetrics

    from html import escape

    from qgis.PyQt.QtWidgets import QLabel, QStyle, QStyleOptionViewItem
except ImportError:
    pass  # QGIS not available, skip Qt widgets

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
    from qgis.core import QgsProject, QgsRasterLayer, QgsLayerTreeLayer, QgsDataSourceUri, QgsHttpHeaders, QgsNetworkAccessManager
except ImportError:
    pass  # QGIS not available, skip this import

from .view_settings import preference

