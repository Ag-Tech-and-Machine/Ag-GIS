"""Native tree navigation regression; synthetic project, isolated profile only."""

import json

import os

from pathlib import Path

import sys



os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

base = Path(os.environ['AGGIS_NAV_SCRATCH']).resolve()

base.mkdir(parents=True, exist_ok=True)

os.environ['QGIS_CUSTOM_CONFIG_PATH'] = str(base / 'config')

os.environ['QGIS_AUTH_DB_DIR_PATH'] = str(base / 'auth')

sys.path.insert(0, os.environ['AGGIS_NAV_PLUGIN_PARENT'])

    pass  # QGIS not available, skip this test

except ImportError:

    from qgis.gui import QgsLayerTreeView

    from qgis.core import QgsApplication, QgsProject, QgsLayerTreeModel, QgsVectorLayer

    from qgis.PyQt.QtTest import QTest

    from qgis.PyQt.QtWidgets import QMainWindow, QDockWidget

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.PyQt.QtCore import Qt, QSettings, QTimer, QPoint
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

from ag_tech_tooling.farm_browser import FarmBrowser

QSettings.setDefaultFormat(QSettings.IniFormat)

for scope in (QSettings.UserScope, QSettings.SystemScope):

    QSettings.setPath(QSettings.IniFormat, scope, str(base / 'settings'))

app = QgsApplication([], False)

app.initQgis()

assert Path(app.qgisSettingsDirPath()).resolve().is_relative_to(base)

auth_path = app.authManager().authenticationDatabasePath()

assert Path(auth_path).resolve().is_relative_to(base)

project = QgsProject.instance()

results = dict(settings=app.qgisSettingsDirPath(), auth=auth_path)

trace = []





def check(case):

    window = QMainWindow()

    dock = QDockWidget('Layers', window)

    view = QgsLayerTreeView()

    model = QgsLayerTreeModel(project.layerTreeRoot())

    model.setFlag(QgsLayerTreeModel.AllowNodeChangeVisibility, True)

    view.setModel(model)

    dock.setWidget(view)

    window.addDockWidget(Qt.LeftDockWidgetArea, dock)

    window.resize(760, 1000)

    class Interface:

        def layerTreeView(self):

            return view

    browser = FarmBrowser(Interface())

    window.show()

    def settle():

        for _ in range(4):

            app.processEvents()

        QTest.qWait(30)

    if os.environ.get('AGGIS_NAV_REOPEN'):

        try:

            path = Path(os.environ['AGGIS_NAV_REOPEN'])

            assert project.read(str(path))

            settle()

            actual = {n.name(): n.isExpanded() for n in project.layerTreeRoot().findGroups(True)}

            expected = json.loads(path.with_suffix('.expansion.json').read_text())

            assert actual == expected, ('Cold process reopen changed expansion', actual, expected)

            results['cold_process_native_reopen'] = True

        finally:

            browser.close()

            window.close()

            project.clear()

            settle()

        return

    def add(parent, name, kind):

        n = parent.addGroup(name)

        n.setCustomProperty('AgTechTooling/kind', kind)

        n.setCustomProperty('AgTechTooling/node', kind + ':' + name)

        n.setExpanded(False)

        return n

    root = project.layerTreeRoot()

    workspace = add(root, 'Farm Data', 'workspace')

    orgs, farms, fields = [], [], []

    for i in range(2):

        org = add(workspace, 'Organisation ' + str(i), 'organisation')

        client = add(org, 'Client ' + str(i), 'client')

        farm = add(client, 'Farm ' + str(i), 'farm')

        orgs.append(org)

        farms.append(farm)

        branch = []

        for j in range(2):

            field = add(farm, f'Field {i}-{j}', 'field')

            add(field, f'Whole Field {i}-{j}', 'whole')

            add(field, f'Seasons {i}-{j}', 'seasons')

            branch.append(field)

        fields.append(branch)

    workspace.setExpanded(True)

    other = root.addGroup('Unrelated manually collapsed')

    other.addGroup('Untouched child')

    other.setExpanded(False)

    layer = QgsVectorLayer('Point?crs=EPSG:4326', 'Unrelated native layer', 'memory')

    project.addMapLayer(layer)

    layer_node = root.findLayer(layer.id())

    layer_node.setItemVisibilityChecked(False)

    project.writeEntry('AgTechTooling', 'schema_version', 2)

    project.writeEntry('AgTechTooling', 'view/focus', True)

    project.writeEntry('AgTechTooling', 'view/zoom', False)

    project.writeEntry('AgTechTooling', 'selected_field', fields[0][0].name())

    root.expandedChanged.connect(lambda n: trace.append((n.name(), n.isExpanded())))

    settle()

    def click(node):

        idx = view.node2index(node)

        view.scrollTo(idx)

        settle()

        rect = view.visualRect(idx)

        assert rect.isValid() and not rect.isEmpty(), node.name()

        QTest.mouseClick(view.viewport(), Qt.LeftButton, Qt.NoModifier,

                         QPoint(rect.right() - 40, rect.center().y()))

        settle()

        assert view.currentNode() is node, ('native click selection', node.name())

    def state():

        return {n.name(): n.isExpanded() for n in root.findGroups(True)}

    try:

        if case == 'preserve':

            for n in root.findGroups(True):

                n.setExpanded(True)

            other.setExpanded(False)

            settle()

            before = state()

            click(fields[0][0])

            assert orgs[1].isExpanded() and fields[1][1].isExpanded(), 'Selecting field collapsed previously open other organisation/field'

            click(fields[1][1])

            assert fields[0][0].isExpanded() and fields[0][1].isExpanded(), 'Selecting another field collapsed comparison fields'

            click(orgs[0])

            assert orgs[1].isExpanded() and fields[1][1].isExpanded(), 'Selecting organisation collapsed another open branch'

            assert not other.isExpanded(), 'Unrelated manual collapse lost'

            fields[0][0].setExpanded(False)

            # The stale saved selected_field must never refocus on refresh.

            snapshot = state()

            browser.layers_added()

            browser.refresh_title()

            settle()

            assert state() == snapshot, 'Deferred presentation refresh changed manual expansion'

            assert view.currentNode() is orgs[0]

            assert not layer_node.itemVisibilityChecked(), 'Navigation changed native visibility'

            results['multiple_organisations_fields_native_clicks'] = True

            results['manual_collapse_deferred_refresh'] = True

            results['native_selection_visibility'] = True

        elif case == 'chain':

            for n in root.findGroups(True):

                n.setExpanded(False)

            workspace.setExpanded(True)

            settle()

            click(orgs[0])

            assert orgs[0].isExpanded() and orgs[0].children()[0].isExpanded() and farms[0].isExpanded(), 'Single-child organisation/client chain did not reach first farm fork'

            assert all(not n.isExpanded() for n in fields[0]), 'First fork arbitrarily expanded a field choice'

            assert not orgs[1].isExpanded()

            click(fields[0][0])

            assert fields[0][0].isExpanded(), 'Clicked field did not reveal choices'

            assert all(not n.isExpanded() for n in fields[0][0].children()), 'Field fork arbitrarily opened Whole Field/Seasons'

            click(fields[0][0].children()[0])

            assert view.currentNode() is fields[0][0].children()[0], 'Leaf click lost selection'

            # Clicking an already selected row also shortcuts after manual collapse.

            click(orgs[0])

            orgs[0].children()[0].setExpanded(False)

            click(orgs[0])

            assert orgs[0].children()[0].isExpanded(), 'Repeated current-row click did not expand chain'

            results['single_child_chain_first_fork_leaf_repeated_click'] = True

        # Native save/read and controller reload must not refocus a saved branch.

        saved = state()

        path = base / ('navigation-' + case + '.qgz')

        assert project.write(str(path))

        path.with_suffix('.expansion.json').write_text(json.dumps(saved, indent=2))

        browser.close()

        browser = FarmBrowser(Interface())

        settle()

        assert state() == saved, 'Controller unload/reload changed expansion'

        assert project.read(str(path))

        settle()

        assert state() == saved, 'Same-process native reopen changed expansion'

        results['unload_reload_same_process_reopen'] = True

        results['saved_project'] = str(path)

    finally:

        browser.close()

        window.close()

        project.clear()

        settle()



try:

    case = os.environ.get('AGGIS_NAV_CASE', 'preserve')

    check(case)

    results['passed'] = True

except BaseException:

    import traceback

    results['error'] = traceback.format_exc()

    raise

finally:

    results['trace'] = trace

    (base / 'assertions.json').write_text(json.dumps(results, indent=2))

    app.exitQgis()

print(json.dumps(results, indent=2))


