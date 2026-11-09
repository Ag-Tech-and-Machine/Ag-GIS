"""Full branded native reopen regression. H_PATH is an isolated fixture directory."""
import os,sys,json,traceback,hashlib
from pathlib import Path
from zipfile import ZipFile
from qgis.core import QgsApplication,QgsProject,QgsCoordinateReferenceSystem,QgsLayerTreeLayer
from qgis.PyQt.QtCore import QTimer,Qt,QPoint,QModelIndex
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtTest import QTest
from qgis.utils import iface,plugins
from ag_tech_tooling.farm_project import create_farm
from ag_tech_tooling import hierarchy as store,managed_data
from ag_tech_tooling import hierarchy_dialog as hd
H=Path(H_PATH).resolve();p=QgsProject.instance();plugin=plugins['ag_tech_tooling'];v=iface.layerTreeView();r={'passed':False,'pid':os.getpid(),'trace':[]}
assert Path(QgsApplication.qgisSettingsDirPath()).resolve().is_relative_to(H)
assert Path(QgsApplication.authManager().authenticationDatabasePath()).resolve().is_relative_to(H)
assert Path(sys.modules['ag_tech_tooling.plugin'].__file__).resolve().is_relative_to(H)
assert plugin.simple_view.switch.isChecked()
# Test-only observation, real methods remain in the call path.
original_show=hd.show_field
original_focus=plugin.browser.focus_node
def show(*a,**kw):
 r['trace'].append({'call':'show_field','field':a[1],'stack':traceback.format_stack(limit=8)});return original_show(*a,**kw)
def focus(n):
 r['trace'].append({'call':'focus_node','key':n.customProperty('AgTechTooling/node',''),'stack':traceback.format_stack(limit=8)});return original_focus(n)
hd.show_field=show;plugin.browser.focus_node=focus
def state():
 def node(n):
  key=n.layerId() if isinstance(n,QgsLayerTreeLayer) else n.customProperty('AgTechTooling/node','') or n.name()
  d={'key':key,'expanded':n.isExpanded(),'checked':n.itemVisibilityChecked()}
  if isinstance(n,QgsLayerTreeLayer):d['subset']=n.layer().subsetString() if hasattr(n.layer(),'subsetString') else '';d['filter_hidden']=n.customProperty('AgTechTooling/filter_hidden',False)
  else:d['children']=[node(c) for c in n.children()]
  return d
 return {'tree':node(p.layerTreeRoot()),'entries':{k:p.readEntry('AgTechTooling',k)[0] for k in ['selected_field','data_filter_field','data_filter_role']},'ids':sorted(p.mapLayers())}
def snap(name):
    # Actual composited desktop before any QWidget rendering.
 import ctypes
 window=int(iface.mainWindow().winId());ctypes.windll.user32.ShowWindow(window,3);ctypes.windll.user32.SetForegroundWindow(window)
 QTest.qWait(200)
 foreground=int(ctypes.windll.user32.GetForegroundWindow())
 r.setdefault('captures',{})[name]={'target_hwnd':window,'foreground_hwnd':foreground,'foreground_matches':foreground==window,'native_view_visible':False}
 from PIL import ImageGrab
 ImageGrab.grab().save(H/(name+'.png'))
 r['captures'][name]['native_view_visible']=False
def store_result(): (H/'result.json').write_text(json.dumps(r,indent=2))
def close_fixture():
 assert not p.fileName() or Path(p.fileName()).resolve().is_relative_to(H)
 assert QApplication.activeModalWidget() is None
 # Only synthetic fixture; no user data or normal session is closed.
 p.setDirty(False);iface.mainWindow().close()
def guard(fn):
 def call():
  try:fn()
  except BaseException:
   r['error']=traceback.format_exc();r['after_failure']=state();store_result();snap('failure');QTimer.singleShot(100,close_fixture)
 return call
@guard
def start():
 global root,first,second
 if globals().get('COLD',False):
  r['before']=json.loads((H/'expected.json').read_text());root=Path(p.fileName()).resolve().parent
  assert root.is_relative_to(H) and root.name=='Synthetic Reopen','Must automatically restore through launcher'
  verify_cold();return
 assert not p.fileName()
 r['cold_empty_visible']=v.isVisible();snap('cold-empty')
 p.setDirty(False)
 root=create_farm(H,'Synthetic Reopen',QgsCoordinateReferenceSystem('EPSG:4326'),organisation='Org A',client='Client A',farm='Farm A',field='Field A',build_tree=True)
 rows=store.records(root);first=rows['field'][0]['id'];org=store.add_record(root,'organisation','Org B');client=store.add_record(root,'client','Client B',org);farm=store.add_record(root,'farm','Farm B',client);second=store.add_record(root,'field','Field B',farm)
 assert iface.addProject(str(root/'Farm.qgz'))
 plugin.backgrounds.choose('none')
 QTimer.singleShot(2000,configure)
@guard
def configure():
 # Use actual managed native disk data under the collapsed first field, like the failing normal map.
 from qgis.core import QgsVectorLayer
 from ag_tech_tooling.import_placement import place_layer
 src=H/'Synthetic samples.geojson';src.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[145,-36]},'properties':{'sample':1}}]}))
 source=QgsVectorLayer(str(src),'Synthetic samples','ogr');assert source.isValid()
 record,saved,created=managed_data.save_dataset(root,source,first,'samples');assert created
 place_layer(root,saved,first,'samples',p)
 hd.show_field(root,first)  # Deliberate initialization, never a row-selection side effect.
 _,nodes=hd.sync_tree(root)
 if globals().get('INDEPENDENT',False):
  # Two actual disk-backed imports, separate fields/organisations, full controller.
  src2=H/'Synthetic second.geojson';src2.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[145.1,-36.1]},'properties':{'sample':2}}]}))
  source2=QgsVectorLayer(str(src2),'Synthetic second','ogr');assert source2.isValid()
  record2,saved2,created2=managed_data.save_dataset(root,source2,second,'samples');assert created2
  place_layer(root,saved2,second,'samples',p)
  # Deliberately show all initialized native references and both imports.
  managed_data.apply_filters(root,'*','*')
  if globals().get('REFERENCE_MODE'):
   seed_references()
  # Disable the separately configurable auto-zoom to isolate visibility/context.
  p.writeEntry('AgTechTooling','view/zoom',False)
  for n in p.layerTreeRoot().findGroups(True):n.setExpanded(True)
  v.setCurrentIndex(QModelIndex());QTimer.singleShot(700,independent_start);return
 # A real name click selects Field B and its native reference context.
 for n in p.layerTreeRoot().findGroups(True):n.setExpanded(True)
 idx=v.node2index(nodes[second]);v.scrollTo(idx);QTest.qWait(150);rect=v.visualRect(idx)
 QTest.mouseClick(v.viewport(),Qt.LeftButton,Qt.NoModifier,QPoint(rect.right()-20,rect.center().y()))
 QTimer.singleShot(1000,comparison)
def visibility_state():
 result=state();result['entries'].pop('selected_field')
 result['extent']=iface.mapCanvas().extent().toString(12)
 result['canvas']=sorted(layer.id() for layer in iface.mapCanvas().layers())
 return result

def click_name(node):
 idx=v.node2index(node);v.scrollTo(idx);QTest.qWait(100);rect=v.visualRect(idx)
 assert rect.isValid()
 QTest.mouseClick(v.viewport(),Qt.LeftButton,Qt.NoModifier,QPoint(rect.right()-20,rect.center().y()))
 QTest.qWait(450)
 assert v.currentNode() is node

def click_check(node):
 from qgis.PyQt.QtWidgets import QStyleOptionViewItem,QStyle
 idx=v.node2index(node);v.scrollTo(idx);QTest.qWait(100)
 option=QStyleOptionViewItem();v.itemDelegate().initStyleOption(option,idx)
 option.rect=v.visualRect(idx);option.widget=v
 rect=v.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator,option,v)
 assert rect.isValid()
 QTest.mouseClick(v.viewport(),Qt.LeftButton,Qt.NoModifier,rect.center());QTest.qWait(450)

@guard
def independent_start():
 assert plugin.simple_view.switch.isChecked()
 assert all(w.isVisible() for w in (v,v.parentWidget(),plugin.browser.dock))
 _,nodes=hd.sync_tree(root)
 a,b=nodes[first],nodes[second]
 imports={n.layer().customProperty('AgTechTooling/import_field'):n for n in p.layerTreeRoot().findLayers() if n.layer().customProperty('AgTechTooling/import_field')}
 assert a.itemVisibilityChecked() and b.itemVisibilityChecked()
 assert imports[first].isVisible() and imports[second].isVisible()
 if globals().get('REFERENCE_MODE'):
  reference_context(a,b,imports);return
 baseline=visibility_state();r['independent_baseline']=baseline
 for n in (a,b,a,b):
  click_name(n)
  r['independent_after_click']=visibility_state()
  assert visibility_state()==baseline,'Row navigation changed field checks/subsets/filter/placement/canvas/extent'
 r['independent_row_navigation']=True
 for org in [n for n in p.layerTreeRoot().findGroups(True) if n.customProperty('AgTechTooling/kind')=='organisation']:
  click_name(org);assert visibility_state()==baseline,'Organisation navigation changed visible fields'
 r['independent_organisation_navigation']=True
 # The first checkbox click changes the current row too: exercise both controllers.
 click_check(a)
 assert not a.itemVisibilityChecked() and b.itemVisibilityChecked()
 assert not imports[first].isVisible() and imports[second].isVisible()
 off=visibility_state();r['independent_off']=off
 assert off['entries']==baseline['entries'] and off['extent']==baseline['extent']
 # Native All Fields views deliberately change their provider subset when A is
 # unchecked. Assert their exact B-only subset, then compare all OTHER state;
 # treating those shared views as unrelated would demand the original bug.
 from qgis.core import QgsExpression
 reference_nodes={n.layerId():n for n in p.layerTreeRoot().findLayers()
                  if n.layer().customProperty('AgTechTooling/all_readonly',False)
                  and n.layer().customProperty('AgTechTooling/table','') in
                  {'agtech_boundaries','agtech_guidance','agtech_infrastructure'}}
 assert len(reference_nodes)==3,'Fixture must exercise all three shared native views'
 expected_subset='"field_id" IN ('+QgsExpression.quotedString(second)+')'
 assert all(n.layer().subsetString()==expected_subset for n in reference_nodes.values()),'Shared reference subset must contain only checked Field B'
 def normalized(s,restore_reference_subset=False):
  s=json.loads(json.dumps(s));s.pop('canvas')
  def visit(n):
   if n['key']=='field:'+first:n['checked']=True
   if restore_reference_subset and n['key'] in reference_nodes:n['subset']=''
   for child in n.get('children',[]):visit(child)
  visit(s['tree']);return s
 assert normalized(off,True)==normalized(baseline),'Tick A off mutated an unrelated branch/subset/expansion'
 r['independent_reference_subset_exact']=True
 click_check(a);assert visibility_state()==baseline,'Tick A on did not independently restore A'
 r['independent_checkbox_off_on']=True
 # Queued refresh must not apply the selected field as an exclusive filter.
 plugin.farms.refresh_current();plugin.browser.layers_added();QTest.qWait(700)
 assert visibility_state()==baseline,'Refresh changed independent visibility'
 r['independent_refresh']=True
 snap('independent-fields')
 # Keep the existing explicit Filter Data acceptance and reload/save/cold coverage.
 click_name(b)
 comparison()

def seed_references():
 from qgis.core import QgsVectorLayer,QgsFeature,QgsGeometry
 for table,shape in [('agtech_boundaries','MULTIPOLYGON ((({x} -36,{x} -35.99,{y} -35.99,{y} -36,{x} -36)))'),('agtech_guidance','MULTILINESTRING (({x} -36,{y} -35.99))')]:
  writer=QgsVectorLayer(store.layer_uri(root,table),'fixture writer','ogr');assert writer.isValid()
  features=[]
  for number,field_id in enumerate((first,second)):
   x=145+number*.1
   feature=QgsFeature(writer.fields());feature['id']='reference-'+str(number);feature['field_id']=field_id;feature['name']='Synthetic '+str(number);feature['revision']='1'
   feature.setGeometry(QgsGeometry.fromWkt(shape.format(x=x,y=x+.01)));features.append(feature)
  assert writer.dataProvider().addFeatures(features)[0]
  writer=None
  layer=next(layer for layer in p.mapLayers().values() if layer.customProperty('AgTechTooling/table')==table)
  layer.reload();layer.updateExtents();assert layer.featureCount()==2
 r['reference_seeded']=True

def reference_context(a,b,imports):
 from qgis.core import QgsRectangle
 from qgis.PyQt.QtWidgets import QDialogButtonBox
 refs=[n.layer() for n in p.layerTreeRoot().findLayers() if n.layer().customProperty('AgTechTooling/table') in ('agtech_boundaries','agtech_guidance')]
 database_before=hashlib.sha256(store.database(root).read_bytes()).hexdigest()
 def reference_fields():return {layer.customProperty('AgTechTooling/table'):sorted(str(f['field_id']) for f in layer.getFeatures()) for layer in refs}
 def expect(fields):
  actual=reference_fields();r['reference_actual']=actual
  assert all(values==sorted(fields) for values in actual.values()),'Shared All Fields references ignored independent field checkbox: '+str(actual)
 def unchanged_context(before):
  assert iface.mapCanvas().extent().toString(12)==before,'Visibility checkbox unexpectedly changed map extent with default zoom on'
  assert b.itemVisibilityChecked() and imports[second].isVisible()
  assert p.readEntry('AgTechTooling','data_filter_field')[0]=='*'
 expect([first,second]);p.writeEntry('AgTechTooling','view/zoom',True)
 if globals().get('REFERENCE_MODE')=='checkbox-context':
  click_name(a)
 iface.mapCanvas().setExtent(QgsRectangle(144.8,-36.3,145.4,-35.8));iface.mapCanvas().refresh();QTest.qWait(300)
 if globals().get('REFERENCE_MODE')!='checkbox-context':v.setCurrentIndex(QModelIndex())
 QTest.qWait(200)
 baseline=iface.mapCanvas().extent().toString(12);r['checkbox_extent_before']=baseline
 click_check(a);r['checkbox_extent_after']=iface.mapCanvas().extent().toString(12)
 assert not a.itemVisibilityChecked() and not imports[first].isVisible()
 if globals().get('REFERENCE_MODE')=='checkbox-context':
  unchanged_context(baseline)
  click_check(a);unchanged_context(baseline);assert imports[first].isVisible()
  v.setFocus();QTest.keyClick(v,Qt.Key_Space);QTest.qWait(450)
  assert not a.itemVisibilityChecked();unchanged_context(baseline)
  QTest.keyClick(v,Qt.Key_Space);QTest.qWait(450)
  assert a.itemVisibilityChecked();unchanged_context(baseline)
  click_check(a);unchanged_context(baseline)
  r['default_zoom_checkbox_context']=True;r['keyboard_checkbox_context']=True
 else:
  expect([second]);unchanged_context(baseline);r['shared_references_independent']=True
  click_check(a);expect([first,second]);unchanged_context(baseline)
  whole=hd.sync_tree(root)[1]['whole:'+first]
  click_check(whole);expect([second]);assert a.itemVisibilityChecked()
  click_check(whole);expect([first,second]);r['shared_whole_field']=True
  # Ancestor visibility is effective visibility; field's own check stays checked.
  org=next(n for n in p.layerTreeRoot().findGroups(True) if n.customProperty('AgTechTooling/kind')=='organisation' and a in n.findGroups(True))
  click_check(org);expect([second]);assert a.itemVisibilityChecked()
  click_check(org);expect([first,second])
  click_check(a);expect([second]);click_check(b);expect([])
  click_check(b);expect([second]);r['shared_parent_and_all_off']=True
  guidance=next(layer for layer in refs if layer.customProperty('AgTechTooling/table')=='agtech_guidance')
  p.layerTreeRoot().findLayer(guidance.id()).setItemVisibilityChecked(False)
  # Deliberate field/type filtering remains independent, restoring checkbox choices.
  plugin.filters.open();d=plugin.filters.dialog
  d.field.setCurrentIndex(d.field.findData(second));d.role.setCurrentIndex(d.role.findData('guidance'))
  QTest.mouseClick(d.findChild(QDialogButtonBox).button(QDialogButtonBox.Apply),Qt.LeftButton)
  assert 'Filter applied' in d.status.text();d.reject();QTest.qWait(500)
  assert all(not layer.readOnly() for layer in refs)
  managed_data.apply_filters(root,'*','*');QTest.qWait(500)
  expect([second]);assert not a.itemVisibilityChecked() and b.itemVisibilityChecked()
  assert not p.layerTreeRoot().findLayer(guidance.id()).itemVisibilityChecked()
  assert all(layer.readOnly() for layer in refs)
  r['reference_explicit_filter_preserved']=True
 assert hashlib.sha256(store.database(root).read_bytes()).hexdigest()==database_before,'Visibility changed original native reference database'
 r['reference_database_unchanged']=True
 # Name navigation still deliberately zooms an already visible dataset.
 click_name(imports[second]);assert iface.mapCanvas().extent().toString(12)!=baseline
 r['name_navigation_zoom_retained']=True
 p.writeEntry('AgTechTooling','view/zoom',False)
 snap('independent-fields');QTimer.singleShot(500,save)

@guard
def comparison():
 assert p.readEntry('AgTechTooling','selected_field')[0]==second
 # Compare all fields, preserve a manually hidden shared reference and mixed expansion.
 if globals().get('COMBINED',False):
  from qgis.PyQt.QtWidgets import QDialogButtonBox
  plugin.filters.open();d=plugin.filters.dialog;assert d.isVisible()
  d.field.setCurrentIndex(d.field.findData(second));d.role.setCurrentIndex(d.role.findData('boundary'))
  QTest.mouseClick(d.findChild(QDialogButtonBox).button(QDialogButtonBox.Apply),Qt.LeftButton)
  assert 'Filter applied' in d.status.text();d.reject()
  assert p.readEntry('AgTechTooling','data_filter_field')[0]==second
  r['specific_filter_ui']=True
  if globals().get('INDEPENDENT',False):
   # A selected, unchecked layer must not undo the explicit filter or tick itself on.
   for n in p.layerTreeRoot().findGroups(True):n.setExpanded(True)
   p.writeEntry('AgTechTooling','view/zoom',True)
   QTest.qWait(500)  # Native canvas bridge applies explicit filter asynchronously.
   baseline=visibility_state();r['filtered_layer_before_click']=baseline
   layer_node=next(n for n in p.layerTreeRoot().findLayers() if n.layer().customProperty('AgTechTooling/import_field')==first)
   assert not layer_node.itemVisibilityChecked()
   click_name(layer_node)
   r['filtered_layer_after_click']=visibility_state()
   assert visibility_state()==baseline,'Selecting filtered/unchecked dataset changed filter/checks/subsets/canvas/extent'
   r['filtered_layer_navigation']=True
   p.writeEntry('AgTechTooling','view/zoom',False)
   click_name(hd.sync_tree(root)[1][second])
 else:
  managed_data.apply_filters(root,'*','boundary');v.setCurrentIndex(QModelIndex())
 QTimer.singleShot(800,save)
@guard
def save():
 _,nodes=hd.sync_tree(root)
 for n in p.layerTreeRoot().findGroups(True):n.setExpanded(True)
 nodes[first].setExpanded(False);nodes['whole:'+second].setExpanded(False)
 native=next(n for n in p.layerTreeRoot().findLayers() if n.layer().customProperty('AgTechTooling/table')=='agtech_boundaries');native.setItemVisibilityChecked(False)
 r['before']=state();r['trace']=[]
 if globals().get('COMBINED',False) and not r.get('reload_preserved'):
  plugin.browser.layers_added();plugin.browser.refresh_title()
  QTimer.singleShot(700,reload_plugin);return
 save_native()
@guard
def reload_plugin():
 global plugin
 assert state()==r['before'],'Queued refresh changed combined state'
 old_browser=plugin.browser;old_farms=plugin.farms
 from qgis.utils import unloadPlugin,loadPlugin,startPlugin
 assert unloadPlugin('ag_tech_tooling')
 assert old_browser.closed and not old_farms.attached
 assert state()==r['before'],'Actual unload changed tree/filter/visibility/reference placement'
 r['actual_unload_preserved']=True
 assert loadPlugin('ag_tech_tooling') and startPlugin('ag_tech_tooling')
 plugin=plugins['ag_tech_tooling']
 QTimer.singleShot(1800,verify_reload)
@guard
def verify_reload():
 from qgis.PyQt.QtWidgets import QToolBar
 assert state()==r['before'],'Full initGui reload changed combined state'
 assert plugin.simple_view.switch.isChecked() and v.isVisible()
 assert all(w.isVisible() for w in [v,v.parentWidget(),plugin.browser.dock])
 assert len([t for t in iface.mainWindow().findChildren(QToolBar) if t.objectName()=='ag_tech_tooling_toolbar'])==1
 r['reload_preserved']=True;snap('reloaded');save_native()
def save_native():
 p.dirtySet.connect(lambda:r['trace'].append({'call':'dirtySet','stack':traceback.format_stack(limit=10)}))
 p.projectSaved.connect(lambda:r['trace'].append({'call':'projectSaved'}))
 r['save_enabled']=iface.actionSaveProject().isEnabled()
 iface.actionSaveProject().trigger()
 QTimer.singleShot(1200,reopen)
@guard
def reopen():
 r['save_state']={'dirty':p.isDirty(),'title':iface.mainWindow().windowTitle(),'modal':str(QApplication.activeModalWidget()),'project':p.fileName()};store_result()
 assert QApplication.activeModalWidget() is None,'Native save conflict'
 if p.isDirty() and r.get('save_retries',0)<2:
  r['save_retries']=r.get('save_retries',0)+1;iface.actionSaveProject().trigger();QTimer.singleShot(1200,reopen);return
 assert not p.isDirty(),'Native save must be clean'
 assert state()==r['before'],'Save changed native state'
 with ZipFile(root/'Farm.qgz') as z:r['saved_xml']=z.read(next(n for n in z.namelist() if n.endswith('.qgs'))).decode()
 snap('saved');r['native_save_clean']=True
 assert iface.addProject(str(root/'Farm.qgz'))
 r['immediate']=state();QTimer.singleShot(2000,verify)
@guard
def verify():
 r['after']=state();r['visible']=v.isVisible();r['simple_view']=plugin.simple_view.switch.isChecked();snap('reopened');store_result()
 assert r['after']==r['before'],'Full native project reopen changed saved expansion/filter/visibility/reference placement'
 assert r['visible'] and r['simple_view']
 r['same_session_reopen']=True
 (H/'expected.json').write_text(json.dumps(r['before'],indent=2))
 from qgis.core import QgsSettings
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
