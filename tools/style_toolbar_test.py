"""Default 294px native toolbar constructor and real overflow contract."""

import os,sys,json,traceback,hashlib

from pathlib import Path

    pass  # QGIS not available, skip this test

except ImportError:

      from qgis.core import QgsCoordinateReferenceSystem

      from ag_tech_tooling.import_placement import place_layer

      from ag_tech_tooling import farm_project,hierarchy,managed_data,operation_style

      source=QgsVectorLayer(str(src),'Synthetic toolbar regression','ogr');check('real fixture valid',source.isValid())

      src=H/'synthetic.geojson';src.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[145,-36]},'properties':{'sample':1}}]}))

      check('exact payload origin',Path(farm_browser.__file__).resolve()==(H/'payload/ag_tech_tooling/farm_browser.py').resolve())

      check('auth isolated post init',Path(QgsApplication.authManager().authenticationDatabasePath()).resolve().is_relative_to(H))

      check('settings isolated post init',Path(QgsApplication.qgisSettingsDirPath()).resolve().is_relative_to(H))

     try:

     global browser,layer,button,toolbar

    def start():

     p.clear();p.setDirty(False);write();iface.mainWindow().close()

     if browser:browser.close();browser=None

     global browser

    def finish():

    sys.excepthook=capture

    def capture(t,v,tb):r['exceptions'].append(''.join(traceback.format_exception(t,v,tb)));write()

     r['assertions'].append(n);write()

     assert v,n

    def check(n,v):

    def write():(E/'result.json').write_text(json.dumps(r,indent=2))

    r={'passed':False,'exceptions':[],'assertions':[],'pid':os.getpid()}

    p=QgsProject.instance();browser=None

    from ag_tech_tooling import farm_browser

    sys.path.insert(0,str(H/'payload'))

    H=Path(os.environ['STYLE_TEST_HOME']);E=Path(os.environ['STYLE_TEST_OUTPUT']);sys.dont_write_bytecode=True

    from qgis.utils import iface

    from qgis.PyQt.QtTest import QTest

    from qgis.PyQt.QtWidgets import QApplication,QToolButton,QMenu,QDialog,QDialogButtonBox,QMessageBox

    from qgis.PyQt.QtCore import Qt,QTimer,QObject,QPoint

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable
try:
        from qgis.core import QgsProject,QgsApplication,QgsVectorLayer,QgsMapLayerStyle
except ImportError:
    pass  # QGIS not available, skip this import

try:

# QGIS imports wrapped to avoid import-time crashes when QGIS is unavailable

  root=farm_project.create_farm(H,'Style Proof',QgsCoordinateReferenceSystem('EPSG:4326'),organisation='Test Org',client='Test Client',farm='Test Farm',field='Test Field',build_tree=True)

  check('native fixture project opened',iface.addProject(str(root/'Farm.qgz')))

  rec,layer,created=managed_data.save_dataset(root,source,hierarchy.records(root)['field'][0]['id'],'samples');check('real managed fixture created',created)

  place_layer(root,layer,rec['field_id'],'samples',p)

  raw=[(f.attributes(),f.geometry().asWkt()) for f in layer.getFeatures()];importxml=managed_data.records(root)[0]['style_xml']

  browser=farm_browser.FarmBrowser(iface);check('constructor succeeds',True)

  iface.mainWindow().showMaximized();browser.dock.setFloating(True);browser.dock.resize(294,600);browser.dock.show()

  view=iface.layerTreeView();view.setCurrentNode(p.layerTreeRoot().findLayer(layer.id()));QTest.qWait(500)

  r['dock_width']=browser.dock.width();check('actual default dock 294px',browser.dock.width()==294)

  button=next(b for _,_,b in browser.buttons if b.text()=='Edit Style…');toolbar=button.parentWidget()

  r['style_visible']=button.isVisible();r['toolbar_actions']=[a.text() for a in toolbar.actions()]

  ext=toolbar.findChild(QToolButton,'qt_toolbar_ext_button');r['extension']={'visible':bool(ext and ext.isVisible()),'enabled':bool(ext and ext.isEnabled())}

  check('defaultwidth actual Edit Style accessible',button.isVisible() or bool(ext and ext.isVisible() and ext.isEnabled()))

  before=QgsMapLayerStyle();before.readFromLayer(layer);sourcehash=hashlib.sha256(src.read_bytes()).hexdigest()

  def cancel():

   try:

    d=QApplication.activeModalWidget();check('native properties visible',d is not None and 'VectorLayerProperties' in d.metaObject().className())

    check('native Symbology visible',any(w.isWidgetType() and w.objectName()=='mOptsPage_Style' and w.isVisible() for w in d.findChildren(QObject)))

    buttons=[]

    for box in d.findChildren(QDialogButtonBox):

     b=box.button(QDialogButtonBox.Cancel);owner=box.parentWidget()

     while owner and not isinstance(owner,QDialog):owner=owner.parentWidget()

     if b and b.isVisible() and b.isEnabled() and owner is d and box.window() is d:buttons.append(b)

    check('unique visible native outer Cancel',len(buttons)==1)

    sizes=[w for w in d.findChildren(QObject) if w.isWidgetType() and w.objectName()=='spinSize' and w.isVisible()]

    check('unique native size editor',len(sizes)==1);sizes[0].setValue(7.75)

    signals=[];d.rejected.connect(lambda:signals.append('rejected'));d.finished.connect(lambda n:signals.append(n));QTest.mouseClick(buttons[0],Qt.LeftButton)

    check('actual Cancel rejected finished0',signals==['rejected',0] and d.result()==0);r['cancel']=True;r['cancel_count']=r.get('cancel_count',0)+1

   except BaseException:capture(*sys.exc_info());finish()

  # Never trigger QAction directly: reach native button or actual extension popup.

  QTimer.singleShot(600,cancel)

  activate('Edit Style…')

  after=QgsMapLayerStyle();after.readFromLayer(layer)

  check('Cancel unchanged native style',before.xmlData()==after.xmlData());check('Cancel unchanged source bytes',hashlib.sha256(src.read_bytes()).hexdigest()==sourcehash)

  check('real native Cancel executed',r.get('cancel') is True);check('zero callback exceptions',r['exceptions']==[])

  from ag_tech_tooling.classification import classify

  layer.setCustomProperty(operation_style.CLASSIFICATION_KEY,json.dumps(classify({'code':'synthetic'},operation='spraying',purpose='operation')))

  def dismiss(expected):

   def ack():

    try:

     d=QApplication.activeModalWidget();check('actual message '+expected,isinstance(d,QMessageBox) and expected in d.text());QTest.mouseClick(d.button(QMessageBox.Ok),Qt.LeftButton)

    except BaseException:capture(*sys.exc_info());finish()

   return ack

  QTimer.singleShot(600,dismiss('has been reset'));activate('Reset to Classification Style…')

  check('classification Reset through native overflow',layer.renderer().symbol().color().name()==operation_style.COLOURS['spraying'])

  def apply():

   try:

    d=QApplication.activeModalWidget();check('second native properties',d is not None and 'VectorLayerProperties' in d.metaObject().className())

    sizes=[w for w in d.findChildren(QObject) if w.isWidgetType() and w.objectName()=='spinSize' and w.isVisible()];check('unique Apply size editor',len(sizes)==1);sizes[0].setValue(4.25)

    bs=[box.button(QDialogButtonBox.Ok) for box in d.findChildren(QDialogButtonBox) if box.isVisible() and box.button(QDialogButtonBox.Ok) and box.button(QDialogButtonBox.Ok).isVisible() and box.window() is d]

    check('unique visible native OK',len(bs)==1);QTest.mouseClick(bs[0],Qt.LeftButton);check('native dialog accepted',d.result()==1)

   except BaseException:capture(*sys.exc_info());finish()

  QTimer.singleShot(600,apply);activate('Edit Style…');check('native deliberate edit applied',layer.renderer().symbol().size()==4.25)

  QTimer.singleShot(600,dismiss('will be saved'));activate('Save Style…')

  check('Save Style observer installed',browser._saved_styles is not None)

  saves=[];p.projectSaved.connect(lambda:saves.append(True))

  savebuttons=[b for b in iface.mainWindow().findChildren(QToolButton) if b.defaultAction() is iface.actionSaveProject() and b.isVisible()]

  check('native Save button visible',len(savebuttons)==1);QTest.mouseClick(savebuttons[0],Qt.LeftButton);QTest.qWait(1500)

  from ag_tech_tooling import dataset_styles

  saved=dataset_styles.latest(root).get(rec['id']);check('real native saved catalogue receipt',bool(saved) and len(saves)==1 and not p.isDirty())

  check('catalogue bound exact final QGZ',saved['project_sha256']==hashlib.sha256((root/'Farm.qgz').read_bytes()).hexdigest())

  browser.close();browser=None;QTest.qWait(100)

  check('native warm reopen',iface.addProject(str(root/'Farm.qgz')));QTest.qWait(500)

  layer=next(l for l in p.mapLayers().values() if l.customProperty('AgTechTooling/dataset_id')==rec['id'])

  check('saved style restored warm',layer.renderer().symbol().size()==4.25)

  check('raw fixture unchanged',[(f.attributes(),f.geometry().asWkt()) for f in layer.getFeatures()]==raw)

  check('original source and import style retained',hashlib.sha256(src.read_bytes()).hexdigest()==sourcehash and managed_data.records(root)[0]['style_xml']==importxml)

  browser=farm_browser.FarmBrowser(iface);browser.dock.resize(294,600);QTest.qWait(300)

  button=next(b for _,_,b in browser.buttons if b.text()=='Edit Style…');toolbar=button.parentWidget();view.setCurrentNode(p.layerTreeRoot().findLayer(layer.id()))

  check('reload no duplicate style actions',len([a for a in toolbar.actions() if a.text()=='Edit Style…'])==1)

  before_reload=QgsMapLayerStyle();before_reload.readFromLayer(layer)

  QTimer.singleShot(600,cancel);activate('Edit Style…');check('reload actual native Cancel',r.get('cancel_count')==2)

  after_reload=QgsMapLayerStyle();after_reload.readFromLayer(layer);check('reload Cancel unchanged style',before_reload.xmlData()==after_reload.xmlData())

  browser.dock.resize(700,600);QTest.qWait(300);check('wide direct primary visible',button.isVisible())

  QTimer.singleShot(600,cancel);activate('Edit Style…');check('wide primary actual Cancel',r.get('cancel_count')==3)

  after_wide=QgsMapLayerStyle();after_wide.readFromLayer(layer);check('wide Cancel unchanged style',before_reload.xmlData()==after_wide.xmlData())

  check('final zero exceptions',r['exceptions']==[])

  r['fixture']=str(root);r['source_sha256']=sourcehash;r['saved_style_revision']=saved['revision'];r['passed']=True

 except BaseException:r['failure']=traceback.format_exc()

 finally:QTimer.singleShot(100,finish)

def activate(text):

 if button.isVisible() and text=='Edit Style…':QTest.mouseClick(button,Qt.LeftButton,pos=QPoint(5,button.height()//2));return

 ext=toolbar.findChild(QToolButton,'qt_toolbar_ext_button')

 check('overflow extension visible enabled',ext is not None and ext.isVisible() and ext.isEnabled())

 def choose():

  try:

   menu=QApplication.activePopupWidget();check('actual overflow popup visible',isinstance(menu,QMenu) and menu.isVisible())

   a=next(a for a in menu.actions() if a.text()=='Edit Style…')

   if a.menu():

    QTest.mouseClick(menu,Qt.LeftButton,pos=menu.actionGeometry(a).center());QTest.qWait(200)

    sub=a.menu();check('actual native style submenu visible',sub.isVisible());target=next(x for x in sub.actions() if x.text()==text);QTest.mouseClick(sub,Qt.LeftButton,pos=sub.actionGeometry(target).center())

   else:QTest.mouseClick(menu,Qt.LeftButton,pos=menu.actionGeometry(a).center())

  except BaseException:capture(*sys.exc_info());finish()

 QTimer.singleShot(100,choose);QTest.mouseClick(ext,Qt.LeftButton);QTest.qWait(100)

QTimer.singleShot(2000,start)


