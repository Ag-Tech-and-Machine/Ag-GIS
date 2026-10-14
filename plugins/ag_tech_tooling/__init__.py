def classFactory(iface):
    """QGIS plugin entry point."""
    from .plugin import AgTechTooling

    return AgTechTooling(iface)
