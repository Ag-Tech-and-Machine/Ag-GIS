"""Full branded native reopen regression. H_PATH is an isolated fixture directory."""

import os,sys,json,traceback,hashlib

from pathlib import Path

from zipfile import ZipFile

    pass  # QGIS not available, skip this test

except ImportError:

     from qgis.core import QgsSettings

     (H/'expected.json').write_text(json.dumps(r['before'],indent=2))

     r['same_session_reopen']=True

     assert r['visible'] and r['simple_view']

     assert r['after']==r['before'],'Full native project reopen changed saved expansion/filter/visibility/reference placement'

     r['after']=state();r['visible']=v.isVisible();r['simple_view']=plugin.simple_view.switch.isChecked();snap('reopened');store_result()

    def verify():

    @guard

     r['immediate']=state();QTimer.singleShot(2000,verify)

     assert iface.addProject(str(root/'Farm.qgz'))

     snap('saved');r['native_save_clean']=True

     with ZipFile(root/'Farm.qgz') as z:r['saved_xml']=z.read(next(n for n in z.namelist() if n.endswith('.qgs'))).decode()

     assert state()==r['before'],'Save changed native state'

     assert not p.isDirty(),'Native save must be clean'

      r['save_retries']=r.get('save_retries',0)+1;iface.actionSaveProject().trigger();QTimer.singleShot(1200,reopen);return

     if p.isDirty() and r.get('save_retries',0)<2:

     assert QApplication.activeModalWidget() is None,'Native save conflict'

     r['save_state']={'dirty':p.isDirty(),'title':iface.mainWindow().windowTitle(),'modal':str(QApplication.activeModalWidget()),'project':p.fileName()};store_result()

    def reopen():

    @guard

     QTimer.singleShot(1200,reopen)

     iface.actionSaveProject().trigger()

     r['save_enabled']=iface.actionSaveProject().isEnabled()

     p.projectSaved.connect(lambda:r['trace'].append({'call':'projectSaved'}))

     p.dirtySet.connect(lambda:r['trace'].append({'call':'dirtySet','stack':traceback.format_stack(limit=10)}))

    def save_native():

     r['reload_preserved']=True;snap('reloaded');save_native()

     assert len([t for t in iface.mainWindow().findChildren(QToolBar) if t.objectName()=='ag_tech_tooling_toolbar'])==1

     assert all(w.isVisible() for w in [v,v.parentWidget(),plugin.browser.dock])

     assert plugin.simple_view.switch.isChecked() and v.isVisible()

     assert state()==r['before'],'Full initGui reload changed combined state'

     from qgis.PyQt.QtWidgets import QToolBar

    def verify_reload():

    @guard

     QTimer.singleShot(1800,verify_reload)

     plugin=plugins['ag_tech_tooling']

     assert loadPlugin('ag_tech_tooling') and startPlugin('ag_tech_tooling')

     r['actual_unload_preserved']=True

     assert state()==r['before'],'Actual unload changed tree/filter/visibility/reference placement'

     assert old_browser.closed and not old_farms.attached

     assert unloadPlugin('ag_tech_tooling')

     from qgis.utils import unloadPlugin,loadPlugin,startPlugin

     old_browser=plugin.browser;old_farms=plugin.farms

     assert state()==r['before'],'Queued refresh changed combined state'

     global plugin

    def reload_plugin():

    @guard

     save_native()

      QTimer.singleShot(700,reload_plugin);return

      plugin.browser.layers_added();plugin.browser.refresh_title()

     if globals().get('COMBINED',False) and not r.get('reload_preserved'):

     r['before']=state();r['trace']=[]

     native=next(n for n in p.layerTreeRoot().findLayers() if n.layer().customProperty('AgTechTooling/table')=='agtech_boundaries');native.setItemVisibilityChecked(False)

     nodes[first].setExpanded(False);nodes['whole:'+second].setExpanded(False)

     for n in p.layerTreeRoot().findGroups(True):n.setExpanded(True)

     _,nodes=hd.sync_tree(root)

    def save():

    @guard

     QTimer.singleShot(800,save)

      managed_data.apply_filters(root,'*','boundary');v.setCurrentIndex(QModelIndex())

     else:

       click_name(hd.sync_tree(root)[1][second])

       p.writeEntry('AgTechTooling','view/zoom',False)

       r['filtered_layer_navigation']=True

       assert visibility_state()==baseline,'Selecting filtered/unchecked dataset changed filter/checks/subsets/canvas/extent'

       r['filtered_layer_after_click']=visibility_state()

       click_name(layer_node)

       assert not layer_node.itemVisibilityChecked()

       layer_node=next(n for n in p.layerTreeRoot().findLayers() if n.layer().customProperty('AgTechTooling/import_field')==first)

       baseline=visibility_state();r['filtered_layer_before_click']=baseline

       QTest.qWait(500)  # Native canvas bridge applies explicit filter asynchronously.

       p.writeEntry('AgTechTooling','view/zoom',True)

       for n in p.layerTreeRoot().findGroups(True):n.setExpanded(True)

       # A selected, unchecked layer must not undo the explicit filter or tick itself on.

      if globals().get('INDEPENDENT',False):

      r['specific_filter_ui']=True

      assert p.readEntry('AgTechTooling','data_filter_field')[0]==second

      assert 'Filter applied' in d.status.text();d.reject()

      QTest.mouseClick(d.findChild(QDialogButtonBox).button(QDialogButtonBox.Apply),Qt.LeftButton)

      d.field.setCurrentIndex(d.field.findData(second));d.role.setCurrentIndex(d.role.findData('boundary'))

      plugin.filters.open();d=plugin.filters.dialog;assert d.isVisible()

      from qgis.PyQt.QtWidgets import QDialogButtonBox

     if globals().get('COMBINED',False):

     # Compare all fields, preserve a manually hidden shared reference and mixed expansion.

     assert p.readEntry('AgTechTooling','selected_field')[0]==second

    def comparison():

    @guard

    

     snap('independent-fields');QTimer.singleShot(500,save)

     p.writeEntry('AgTechTooling','view/zoom',False)

     r['name_navigation_zoom_retained']=True

     click_name(imports[second]);assert iface.mapCanvas().extent().toString(12)!=baseline

     # Name navigation still deliberately zooms an already visible dataset.

     r['reference_database_unchanged']=True

     assert hashlib.sha256(store.database(root).read_bytes()).hexdigest()==database_before,'Visibility changed original native reference database'

      r['reference_explicit_filter_preserved']=True

      assert all(layer.readOnly() for layer in refs)

      assert not p.layerTreeRoot().findLayer(guidance.id()).itemVisibilityChecked()

      expect([second]);assert not a.itemVisibilityChecked() and b.itemVisibilityChecked()

      managed_data.apply_filters(root,'*','*');QTest.qWait(500)

      assert all(not layer.readOnly() for layer in refs)

      assert 'Filter applied' in d.status.text();d.reject();QTest.qWait(500)

      QTest.mouseClick(d.findChild(QDialogButtonBox).button(QDialogButtonBox.Apply),Qt.LeftButton)

      d.field.setCurrentIndex(d.field.findData(second));d.role.setCurrentIndex(d.role.findData('guidance'))

      plugin.filters.open();d=plugin.filters.dialog

      # Deliberate field/type filtering remains independent, restoring checkbox choices.

      p.layerTreeRoot().findLayer(guidance.id()).setItemVisibilityChecked(False)

      guidance=next(layer for layer in refs if layer.customProperty('AgTechTooling/table')=='agtech_guidance')

      click_check(b);expect([second]);r['shared_parent_and_all_off']=True

      click_check(a);expect([second]);click_check(b);expect([])

      click_check(org);expect([first,second])

      click_check(org);expect([second]);assert a.itemVisibilityChecked()

      org=next(n for n in p.layerTreeRoot().findGroups(True) if n.customProperty('AgTechTooling/kind')=='organisation' and a in n.findGroups(True))

      # Ancestor visibility is effective visibility; field's own check stays checked.

      click_check(whole);expect([first,second]);r['shared_whole_field']=True

      click_check(whole);expect([second]);assert a.itemVisibilityChecked()

      whole=hd.sync_tree(root)[1]['whole:'+first]

      click_check(a);expect([first,second]);unchanged_context(baseline)

      expect([second]);unchanged_context(baseline);r['shared_references_independent']=True

     else:

      r['default_zoom_checkbox_context']=True;r['keyboard_checkbox_context']=True

      click_check(a);unchanged_context(baseline)

      assert a.itemVisibilityChecked();unchanged_context(baseline)

      QTest.keyClick(v,Qt.Key_Space);QTest.qWait(450)

      assert not a.itemVisibilityChecked();unchanged_context(baseline)

      v.setFocus();QTest.keyClick(v,Qt.Key_Space);QTest.qWait(450)

      click_check(a);unchanged_context(baseline);assert imports[first].isVisible()

      unchanged_context(baseline)

     if globals().get('REFERENCE_MODE')=='checkbox-context':

     assert not a.itemVisibilityChecked() and not imports[first].isVisible()

     click_check(a);r['checkbox_extent_after']=iface.mapCanvas().extent().toString(12)

     baseline=iface.mapCanvas().extent().toString(12);r['checkbox_extent_before']=baseline

     QTest.qWait(200)

     if globals().get('REFERENCE_MODE')!='checkbox-context':v.setCurrentIndex(QModelIndex())

     iface.mapCanvas().setExtent(QgsRectangle(144.8,-36.3,145.4,-35.8));iface.mapCanvas().refresh();QTest.qWait(300)

      click_name(a)

     if globals().get('REFERENCE_MODE')=='checkbox-context':

     expect([first,second]);p.writeEntry('AgTechTooling','view/zoom',True)

      assert p.readEntry('AgTechTooling','data_filter_field')[0]=='*'

      assert b.itemVisibilityChecked() and imports[second].isVisible()

      assert iface.mapCanvas().extent().toString(12)==before,'Visibility checkbox unexpectedly changed map extent with default zoom on'

     def unchanged_context(before):

      assert all(values==sorted(fields) for values in actual.values()),'Shared All Fields references ignored independent field checkbox: '+str(actual)

      actual=reference_fields();r['reference_actual']=actual

     def expect(fields):

     def reference_fields():return {layer.customProperty('AgTechTooling/table'):sorted(str(f['field_id']) for f in layer.getFeatures()) for layer in refs}

     database_before=hashlib.sha256(store.database(root).read_bytes()).hexdigest()

     refs=[n.layer() for n in p.layerTreeRoot().findLayers() if n.layer().customProperty('AgTechTooling/table') in ('agtech_boundaries','agtech_guidance')]

     from qgis.PyQt.QtWidgets import QDialogButtonBox

     from qgis.core import QgsRectangle

    def reference_context(a,b,imports):

    

     r['reference_seeded']=True

      layer.reload();layer.updateExtents();assert layer.featureCount()==2

      layer=next(layer for layer in p.mapLayers().values() if layer.customProperty('AgTechTooling/table')==table)

      writer=None

      assert writer.dataProvider().addFeatures(features)[0]

       feature.setGeometry(QgsGeometry.fromWkt(shape.format(x=x,y=x+.01)));features.append(feature)

       feature=QgsFeature(writer.fields());feature['id']='reference-'+str(number);feature['field_id']=field_id;feature['name']='Synthetic '+str(number);feature['revision']='1'

       x=145+number*.1

      for number,field_id in enumerate((first,second)):

      features=[]

      writer=QgsVectorLayer(store.layer_uri(root,table),'fixture writer','ogr');assert writer.isValid()

     for table,shape in [('agtech_boundaries','MULTIPOLYGON ((({x} -36,{x} -35.99,{y} -35.99,{y} -36,{x} -36)))'),('agtech_guidance','MULTILINESTRING (({x} -36,{y} -35.99))')]:

     from qgis.core import QgsVectorLayer,QgsFeature,QgsGeometry

    def seed_references():

    

     comparison()

     click_name(b)

     # Keep the existing explicit Filter Data acceptance and reload/save/cold coverage.

     snap('independent-fields')

     r['independent_refresh']=True

     assert visibility_state()==baseline,'Refresh changed independent visibility'

     plugin.farms.refresh_current();plugin.browser.layers_added();QTest.qWait(700)

     # Queued refresh must not apply the selected field as an exclusive filter.

     r['independent_checkbox_off_on']=True

     click_check(a);assert visibility_state()==baseline,'Tick A on did not independently restore A'

     r['independent_reference_subset_exact']=True

     assert normalized(off,True)==normalized(baseline),'Tick A off mutated an unrelated branch/subset/expansion'

      visit(s['tree']);return s

       for child in n.get('children',[]):visit(child)

       if restore_reference_subset and n['key'] in reference_nodes:n['subset']=''

       if n['key']=='field:'+first:n['checked']=True

      def visit(n):

      s=json.loads(json.dumps(s));s.pop('canvas')

     def normalized(s,restore_reference_subset=False):

     assert all(n.layer().subsetString()==expected_subset for n in reference_nodes.values()),'Shared reference subset must contain only checked Field B'

     expected_subset='"field_id" IN ('+QgsExpression.quotedString(second)+')'

     assert len(reference_nodes)==3,'Fixture must exercise all three shared native views'

                      {'agtech_boundaries','agtech_guidance','agtech_infrastructure'}}

                      and n.layer().customProperty('AgTechTooling/table','') in

                      if n.layer().customProperty('AgTechTooling/all_readonly',False)

     reference_nodes={n.layerId():n for n in p.layerTreeRoot().findLayers()

     from qgis.core import QgsExpression

     # treating those shared views as unrelated would demand the original bug.

     # unchecked. Assert their exact B-only subset, then compare all OTHER state;

     # Native All Fields views deliberately change their provider subset when A is

     assert off['entries']==baseline['entries'] and off['extent']==baseline['extent']

     off=visibility_state();r['independent_off']=off

     assert not imports[first].isVisible() and imports[second].isVisible()

     assert not a.itemVisibilityChecked() and b.itemVisibilityChecked()

     click_check(a)

     # The first checkbox click changes the current row too: exercise both controllers.

     r['independent_organisation_navigation']=True

      click_name(org);assert visibility_state()==baseline,'Organisation navigation changed visible fields'

     for org in [n for n in p.layerTreeRoot().findGroups(True) if n.customProperty('AgTechTooling/kind')=='organisation']:

     r['independent_row_navigation']=True

      assert visibility_state()==baseline,'Row navigation changed field checks/subsets/filter/placement/canvas/extent'

      r['independent_after_click']=visibility_state()

      click_name(n)

     for n in (a,b,a,b):

     baseline=visibility_state();r['independent_baseline']=baseline

      reference_context(a,b,imports);return

     if globals().get('REFERENCE_MODE'):

     assert imports[first].isVisible() and imports[second].isVisible()

     assert a.itemVisibilityChecked() and b.itemVisibilityChecked()

     imports={n.layer().customProperty('AgTechTooling/import_field'):n for n in p.layerTreeRoot().findLayers() if n.layer().customProperty('AgTechTooling/import_field')}

     a,b=nodes[first],nodes[second]

     _,nodes=hd.sync_tree(root)

     assert all(w.isVisible() for w in (v,v.parentWidget(),plugin.browser.dock))

     assert plugin.simple_view.switch.isChecked()

    def independent_start():

    @guard

    

     QTest.mouseClick(v.viewport(),Qt.LeftButton,Qt.NoModifier,rect.center());QTest.qWait(450)

     assert rect.isValid()

     rect=v.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator,option,v)

     option.rect=v.visualRect(idx);option.widget=v

     option=QStyleOptionViewItem();v.itemDelegate().initStyleOption(option,idx)

     idx=v.node2index(node);v.scrollTo(idx);QTest.qWait(100)

     from qgis.PyQt.QtWidgets import QStyleOptionViewItem,QStyle

    def click_check(node):

    

     assert v.currentNode() is node

     QTest.qWait(450)

     QTest.mouseClick(v.viewport(),Qt.LeftButton,Qt.NoModifier,QPoint(rect.right()-20,rect.center().y()))

     assert rect.isValid()

     idx=v.node2index(node);v.scrollTo(idx);QTest.qWait(100);rect=v.visualRect(idx)

    def click_name(node):

    

     return result

     result['canvas']=sorted(layer.id() for layer in iface.mapCanvas().layers())

     result['extent']=iface.mapCanvas().extent().toString(12)

     result=state();result['entries'].pop('selected_field')

    def visibility_state():

     QTimer.singleShot(1000,comparison)

     QTest.mouseClick(v.viewport(),Qt.LeftButton,Qt.NoModifier,QPoint(rect.right()-20,rect.center().y()))

     idx=v.node2index(nodes[second]);v.scrollTo(idx);QTest.qWait(150);rect=v.visualRect(idx)

     for n in p.layerTreeRoot().findGroups(True):n.setExpanded(True)

     # A real name click selects Field B and its native reference context.

      v.setCurrentIndex(QModelIndex());QTimer.singleShot(700,independent_start);return

      for n in p.layerTreeRoot().findGroups(True):n.setExpanded(True)

      p.writeEntry('AgTechTooling','view/zoom',False)

      # Disable the separately configurable auto-zoom to isolate visibility/context.

       seed_references()

      if globals().get('REFERENCE_MODE'):

      managed_data.apply_filters(root,'*','*')

      # Deliberately show all initialized native references and both imports.

      place_layer(root,saved2,second,'samples',p)

      record2,saved2,created2=managed_data.save_dataset(root,source2,second,'samples');assert created2

      source2=QgsVectorLayer(str(src2),'Synthetic second','ogr');assert source2.isValid()

      src2=H/'Synthetic second.geojson';src2.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[145.1,-36.1]},'properties':{'sample':2}}]}))

      # Two actual disk-backed imports, separate fields/organisations, full controller.

     if globals().get('INDEPENDENT',False):

     _,nodes=hd.sync_tree(root)

     hd.show_field(root,first)  # Deliberate initialization, never a row-selection side effect.

     place_layer(root,saved,first,'samples',p)

     record,saved,created=managed_data.save_dataset(root,source,first,'samples');assert created

     source=QgsVectorLayer(str(src),'Synthetic samples','ogr');assert source.isValid()

     src=H/'Synthetic samples.geojson';src.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[145,-36]},'properties':{'sample':1}}]}))

     from ag_tech_tooling.import_placement import place_layer

     from qgis.core import QgsVectorLayer

     # Use actual managed native disk data under the collapsed first field, like the failing normal map.

    def configure():

    @guard

     QTimer.singleShot(2000,configure)

     plugin.backgrounds.choose('none')

     assert iface.addProject(str(root/'Farm.qgz'))

     rows=store.records(root);first=rows['field'][0]['id'];org=store.add_record(root,'organisation','Org B');client=store.add_record(root,'client','Client B',org);farm=store.add_record(root,'farm','Farm B',client);second=store.add_record(root,'field','Field B',farm)

     root=create_farm(H,'Synthetic Reopen',QgsCoordinateReferenceSystem('EPSG:4326'),organisation='Org A',client='Client A',farm='Farm A',field='Field A',build_tree=True)

     p.setDirty(False)

     r['cold_empty_visible']=v.isVisible();snap('cold-empty')

     assert not p.fileName()

      verify_cold();return

      assert root.is_relative_to(H) and root.name=='Synthetic Reopen','Must automatically restore through launcher'

      r['before']=json.loads((H/'expected.json').read_text());root=Path(p.fileName()).resolve().parent

     if globals().get('COLD',False):

     global root,first,second

    def start():

    @guard

     return call

       r['error']=traceback.format_exc();r['after_failure']=state();store_result();snap('failure');QTimer.singleShot(100,close_fixture)

      except BaseException:

      try:fn()

     def call():

    def guard(fn):

     p.setDirty(False);iface.mainWindow().close()

     # Only synthetic fixture; no user data or normal session is closed.

     assert QApplication.activeModalWidget() is None

     assert not p.fileName() or Path(p.fileName()).resolve().is_relative_to(H)

    def close_fixture():

    def store_result(): (H/'result.json').write_text(json.dumps(r,indent=2))

     r['captures'][name]['native_view_visible']=False

     ImageGrab.grab().save(H/(name+'.png'))

     from PIL import ImageGrab

     r.setdefault('captures',{})[name]={'target_hwnd':window,'foreground_hwnd':foreground,'foreground_matches':foreground==window,'native_view_visible':False}

     foreground=int(ctypes.windll.user32.GetForegroundWindow())

     QTest.qWait(200)

     window=int(iface.mainWindow().winId());ctypes.windll.user32.ShowWindow(window,3);ctypes.windll.user32.SetForegroundWindow(window)

     import ctypes

        # Actual composited desktop before any QWidget rendering.

    def snap(name):

     return {'tree':node(p.layerTreeRoot()),'entries':{k:p.readEntry('AgTechTooling',k)[0] for k in ['selected_field','data_filter_field','data_filter_role']},'ids':sorted(p.mapLayers())}

      return d

      else:d['children']=[node(c) for c in n.children()]

      if isinstance(n,QgsLayerTreeLayer):d['subset']=n.layer().subsetString() if hasattr(n.layer(),'subsetString') else '';d['filter_hidden']=n.customProperty('AgTechTooling/filter_hidden',False)

      d={'key':key,'expanded':n.isExpanded(),'checked':n.itemVisibilityChecked()}

      key=n.layerId() if isinstance(n,QgsLayerTreeLayer) else n.customProperty('AgTechTooling/node','') or n.name()

     def node(n):

    def state():

    hd.show_field=show;plugin.browser.focus_node=focus

     r['trace'].append({'call':'focus_node','key':n.customProperty('AgTechTooling/node',''),'stack':traceback.format_stack(limit=8)});return original_focus(n)

    def focus(n):

     r['trace'].append({'call':'show_field','field':a[1],'stack':traceback.format_stack(limit=8)});return original_show(*a,**kw)

    def show(*a,**kw):

    original_focus=plugin.browser.focus_node

    original_show=hd.show_field

    # Test-only observation, real methods remain in the call path.

    assert plugin.simple_view.switch.isChecked()

    assert Path(sys.modules['ag_tech_tooling.plugin'].__file__).resolve().is_relative_to(H)

    assert Path(QgsApplication.authManager().authenticationDatabasePath()).resolve().is_relative_to(H)

    assert Path(QgsApplication.qgisSettingsDirPath()).resolve().is_relative_to(H)

    H=Path(H_PATH).resolve();p=QgsProject.instance();plugin=plugins['ag_tech_tooling'];v=iface.layerTreeView();r={'passed':False,'pid':os.getpid(),'trace':[]}

    from ag_tech_tooling import hierarchy_dialog as hd

    from ag_tech_tooling import hierarchy as store,managed_data

    from ag_tech_tooling.farm_project import create_farm

    from qgis.utils import iface,plugins

    from qgis.PyQt.QtTest import QTest

    from qgis.PyQt.QtWidgets import QApplication

    from qgis.PyQt.QtCore import QTimer,Qt,QPoint,QModelIndex

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsApplication,QgsProject,QgsCoordinateReferenceSystem,QgsLayerTreeLayer
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

 QgsSettings().setValue('qgis/projOpenAtLaunch',1)

 # The same controller must still honour a genuine navigation gesture after restoration.

 _,nodes=hd.sync_tree(root);idx=v.node2index(nodes[first]);v.scrollTo(idx);QTest.qWait(100);rect=v.visualRect(idx)

 QTest.mouseClick(v.viewport(),Qt.LeftButton,Qt.NoModifier,QPoint(rect.right()-20,rect.center().y()))

 QTimer.singleShot(700,verify_click)

@guard

def verify_click():

 assert p.readEntry('AgTechTooling','data_filter_field')[0]==r['before']['entries']['data_filter_field'],'Post-reopen navigation changed deliberate filter'

 assert p.readEntry('AgTechTooling','selected_field')[0]==first,'Post-reopen click did not update browsing context'

 _,nodes=hd.sync_tree(root);assert nodes[first].isExpanded() and nodes[second].isExpanded()

 r['post_reopen_explicit_click']=True

 # Do not overwrite the saved comparison-state fixture; close only this synthetic dirty map.

 r['passed']=True;r['passed_at_step']='final';store_result();QTimer.singleShot(100,close_fixture)

@guard

def verify_cold():

 assert state()==r['before'],'Cold automatic native reopen changed saved expansion/filter/visibility/reference placement'

 assert v.isVisible() and plugin.simple_view.switch.isChecked()

 snap('cold-restored');r['cold_automatic_restore']=True;r['passed']=True;store_result();QTimer.singleShot(100,close_fixture)

QTimer.singleShot(300,start)


