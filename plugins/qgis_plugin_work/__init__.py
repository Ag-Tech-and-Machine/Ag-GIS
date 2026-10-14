def classFactory(iface):
    """QGIS plugin entry point."""
    from .plugin import PluginWork

    return PluginWork(iface)
