# SPDX-License-Identifier: GPL-2.0-or-later
"""Farm-specific presentation on the existing native QGIS Layers view."""
from html import escape
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QDockWidget, QStyle, QStyledItemDelegate, QStyleOptionViewItem, QToolTip
from qgis.core import QgsLayerTreeGroup, QgsProject
from .ui_icons import icon


KINDS = {
    "workspace": ("folder", "Farm Data"),
    "organisation": ("organisation", "Organisation"),
    "client": ("client", "Client"),
    "farm": ("farm", "Farm"),
    "field": ("field", "Field"),
    "whole": ("whole", "Whole Field"),
    "seasons": ("season", "Seasons"),
    "season": ("season", "Season"),
    "crop": ("crop", "Crop"),
    "plans": ("plan", "Plans"),
    "operations": ("job", "Operations"),
    "results": ("result", "Results"),
}


class FarmTreeDelegate(QStyledItemDelegate):
    """Decorate managed groups; forward native layer/legend/editor behaviour."""

    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.native = view.itemDelegate()
        self.connections = ((self.native.commitData, self.commitData.emit),
                            (self.native.closeEditor, self.closeEditor.emit),
                            (self.native.sizeHintChanged, self.sizeHintChanged.emit))
        for signal, callback in self.connections:
            signal.connect(callback)

    def kind(self, index):
        node = self.view.index2node(index)
        if not isinstance(node, QgsLayerTreeGroup):
            return None
        kind = node.customProperty("AgTechTooling/kind", "")
        if not kind and node.customProperty("AgTechTooling/workspace", ""):
            kind = "workspace"
        return kind if isinstance(kind, str) and kind in KINDS else None

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        kind = self.kind(index)
        if kind:
            option.icon = icon(KINDS[kind][0])
            option.decorationSize = QSize(20, 20)
            if kind in {"workspace", "organisation"}:
                option.font.setBold(True)

    def paint(self, painter, option, index):
        if not self.kind(index):
            return self.native.paint(painter, option, index)
        decorated = QStyleOptionViewItem(option)
        self.initStyleOption(decorated, index)
        style = decorated.widget.style() if decorated.widget else self.view.style()
        style.drawControl(QStyle.CE_ItemViewItem, decorated, painter, decorated.widget)

    def sizeHint(self, option, index):
        size = self.native.sizeHint(option, index)
        return QSize(size.width(), max(26, size.height())) if self.kind(index) else size

    def helpEvent(self, event, view, option, index):
        kind = self.kind(index)
        if not kind:
            return self.native.helpEvent(event, view, option, index)
        node = self.view.index2node(index)
        QToolTip.showText(event.globalPos(), f"<b>{KINDS[kind][1]}</b><br>{escape(node.name())}", view)
        return True

    def editorEvent(self, event, model, option, index):
        return self.native.editorEvent(event, model, option, index)

    def createEditor(self, parent, option, index):
        return self.native.createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        self.native.setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        self.native.setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        self.native.updateEditorGeometry(editor, option, index)

    def destroyEditor(self, editor, index):
        self.native.destroyEditor(editor, index)

    def close(self):
        for signal, callback in self.connections:
            signal.disconnect(callback)


class FarmBrowser:
    """Install and fully restore the presentation without replacing the model."""

    def __init__(self, iface):
        self.view = iface.layerTreeView() if hasattr(iface, "layerTreeView") else None
        self.delegate = None
        self.dock = None
        if self.view is None:
            return
        self.indentation = self.view.indentation()
        self.icon_size = self.view.iconSize()
        self.delegate = FarmTreeDelegate(self.view)
        self.view.setItemDelegate(self.delegate)
        self.view.setIndentation(14)
        self.view.setIconSize(QSize(20, 20))
        parent = self.view.parentWidget()
        while parent is not None and not isinstance(parent, QDockWidget):
            parent = parent.parentWidget()
        self.dock = parent
        self.dock_title = self.dock.windowTitle() if self.dock else ""
        QgsProject.instance().readProject.connect(self.refresh_title)
        QgsProject.instance().cleared.connect(self.refresh_title)
        self.refresh_title()

    def refresh_title(self, *args):
        if self.dock is not None:
            farm = QgsProject.instance().readNumEntry("AgTechTooling", "schema_version")[0] == 2
            self.dock.setWindowTitle("Farm Data" if farm else self.dock_title)

    def close(self):
        if self.delegate is None:
            return
        if self.view.itemDelegate() is self.delegate:
            self.view.setItemDelegate(self.delegate.native)
        self.view.setIndentation(self.indentation)
        self.view.setIconSize(self.icon_size)
        QgsProject.instance().readProject.disconnect(self.refresh_title)
        QgsProject.instance().cleared.disconnect(self.refresh_title)
        if self.dock is not None:
            self.dock.setWindowTitle(self.dock_title)
        self.delegate.close()
        self.delegate.deleteLater()
        self.delegate = None
