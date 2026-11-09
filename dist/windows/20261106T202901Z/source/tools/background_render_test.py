"""Native canvas/bridge rendering and cancellation against local coloured tiles.

No public tile downloads: the native request preprocessor routes test requests
to an ephemeral localhost server, including provider worker-thread requests.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
sys.path.insert(0, os.environ.get("AGTECH_TEST_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1]/"plugins")))
from qgis.PyQt.QtCore import QUrl, QBuffer, QIODevice
from qgis.PyQt.QtGui import QImage, QColor
from qgis.PyQt.QtWidgets import QMainWindow, QLabel
from qgis.PyQt.QtTest import QTest
from qgis.core import (QgsApplication, QgsProject, QgsNetworkAccessManager,
                       QgsCoordinateReferenceSystem, QgsRectangle)
from qgis.gui import QgsMapCanvas, QgsLayerTreeMapCanvasBridge
from ag_tech_tooling.background_maps import BackgroundMaps, ensure_background

app=QgsApplication([],False);app.initQgis();project=QgsProject.instance()
colours=dict(osm="#80c0ff",satellite_au="#509050",satellite_world="#c09050",esri_world="#7080a0")
images={};requests=[];slow=False
for key,colour in colours.items():
    image=QImage(256,256,QImage.Format_RGB32);image.fill(QColor(colour))
    buffer=QBuffer();buffer.open(QIODevice.WriteOnly);assert image.save(buffer,"PNG")
    images[key]=bytes(buffer.data())

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        key,zoom=self.path.strip("/").split("/")[:2]
        requests.append((key,int(zoom)))
        if slow and key=="satellite_world":time.sleep(0.6)
        data=images[key];self.send_response(200);self.send_header("Content-Type","image/png")
        self.send_header("Content-Length",str(len(data)));self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass  # Cancelled native render.
    def log_message(self,*args):pass

server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
def route(request):
    url=request.url();host=url.host();path=url.path()
    if host=="tile.openstreetmap.org":key="osm";zoom=path.split("/")[1]
    elif host=="ows.dea.ga.gov.au":key="satellite_au";zoom=parse_qs(urlparse(url.toString()).query)["tilematrix"][0]
    elif host=="tiles.maps.eox.at":key="satellite_world";zoom=path.split("/")[-3]
    elif host=="services.arcgisonline.com":key="esri_world";zoom=path.split("/")[-3]
    else:return
    request.setUrl(QUrl(f"http://127.0.0.1:{server.server_port}/{key}/{zoom}/{path.rsplit('/',1)[-1]}"))
processor=QgsNetworkAccessManager.setRequestPreprocessor(route)
class Interface:
    def __init__(self):
        self.window=QMainWindow();self.canvas=QgsMapCanvas();self.canvas.setRenderFlag(False)
        self.window.setCentralWidget(self.canvas);self.window.resize(500,400)
        self.canvas.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
        self.bridge=QgsLayerTreeMapCanvasBridge(project.layerTreeRoot(),self.canvas)
        self.bridge.setAutoSetupOnFirstLayer(False)
    def mainWindow(self):return self.window
    def mapCanvas(self):return self.canvas

def wait_until(predicate):
    deadline=time.monotonic()+12
    while not predicate() and time.monotonic()<deadline:QTest.qWait(20)
    assert predicate(),"Native canvas did not reach the expected rendered state"

iface=Interface();controller=None
try:
    project.writeEntry("AgTechTooling","schema_version",2);ensure_background()
    controller=BackgroundMaps(iface);iface.window.show();QTest.qWait(30)
    # Close farm scale: providers must reuse their supported matrix, not request
    # unsupported higher levels. This was a blank DEA map at z15–17.
    iface.canvas.setExtent(QgsRectangle(16170700,-4377200,16171000,-4376900))
    controller.choose("none");QTest.qWait(30);iface.canvas.setRenderFlag(True)
    def colour():
        image=iface.canvas.grab().toImage()
        return image.pixelColor(image.width()//2,image.height()//2).name()
    for key in colours:
        controller.choose(key)
        wait_until(lambda: not iface.canvas.isDrawing() and colour()==colours[key])
        assert controller.visible_providers()==[key]
        assert [l.customProperty("AgTechTooling/background") for l in iface.canvas.layers()]==[key]
    assert all(zoom<=14 for key,zoom in requests if key.startswith("satellite_")),requests
    assert {key for key,zoom in requests}==set(colours)
    # New extent forces uncached slow world tiles, then change twice before they
    # arrive. The final checkbox, layer list, preference and pixels must agree.
    controller.choose("osm")
    wait_until(lambda:not iface.canvas.isDrawing() and colour()==colours["osm"])
    slow=True;before=len(requests)
    iface.canvas.setExtent(QgsRectangle(16175000,-4377500,16175300,-4377200))
    controller.choose("satellite_world");iface.canvas.refresh()
    wait_until(lambda:any(key=="satellite_world" for key,zoom in requests[before:]))
    # QGIS keeps the previous completed map image during asynchronous rendering.
    # Never present that old background as the newly checked selection.
    transition=iface.canvas.findChild(QLabel,"ag_tech_tooling_background_transition")
    assert transition is not None and transition.isVisible(), "Old backdrop must be covered until the selected background finishes rendering"
    assert "Satellite" in transition.text() and "background" in transition.text().lower()
    assert colour()!=colours["satellite_world"], "The new tiles are deliberately still loading"
    assert colour()!=colours["osm"], "A tick for World must not display the previous Roads map as current"
    controller.choose("satellite_au");controller.choose("osm")
    wait_until(lambda:not iface.canvas.isDrawing() and colour()==colours["osm"])
    assert not transition.isVisible(), "Only a completed render of the latest choice may uncover the map"
    QTest.qWait(900)
    assert colour()==colours["osm"] and controller.visible_providers()==["osm"]
    controller.choose("none");wait_until(lambda:not iface.canvas.layers() and colour()=="#ffffff")
    controller.close();controller=None;QTest.qWait(30)
    print("Native canvas pixels, close-scale zoom limits, rapid switching, cancelled slow tiles and no-background rendering passed (localhost only)")
finally:
    if controller:controller.close()
    iface.canvas.stopRendering();iface.canvas.setRenderFlag(False);iface.window.close()
    project.clear();QgsNetworkAccessManager.removeRequestPreprocessor(processor)
    server.shutdown();server.server_close();thread.join();app.exitQgis()
