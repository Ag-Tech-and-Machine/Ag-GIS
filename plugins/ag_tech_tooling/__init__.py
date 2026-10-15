# SPDX-License-Identifier: GPL-2.0-or-later
def classFactory(iface):
    """QGIS plugin entry point."""
    from .plugin import AgTechTooling

    return AgTechTooling(iface)
