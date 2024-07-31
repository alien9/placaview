from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject, QgsApplication
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal, QUrl, QSize
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget, QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox, QComboBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit, QTextEdit,  QFormLayout,  QHBoxLayout, QGraphicsView, QVBoxLayout, QApplication, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from qgis.PyQt import uic
from qgis.PyQt.QtSvg import QGraphicsSvgItem, QSvgRenderer, QSvgWidget
import qgis.PyQt.QtSvg
from qgis.PyQt.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from qgis.PyQt.QtSvg import QSvgWidget, QSvgRenderer
from qgis.PyQt.QtGui import QTransform, QColor
from .placa_selector import PlacaSelector
from qgis.core import *
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsTask)
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.gui import QgsMapCanvas, QgsMapToolIdentifyFeature
from .equidistance_buffer import EquidistanceBuffer
from qgis.gui import QgsFilterLineEdit
import os
import requests
import re
import json
import datetime
from .roads_selector import RoadsSelector
        
FormClass, eck = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'signs_editor.ui'))


class SignDataDownloader(QgsTask):
    key = None
    image_id = None
    result = None
    road_id: int = None
    road_name: str = None

    def run(self):
        try:
            r = requests.get(
                f"https://graph.mapillary.com/{self.image_id}?access_token={self.key}&fields={self.fields}")
            if r.status_code == 200:
                self.result = r.json()
                return True
            print("problem")
            print(r.status_code)
            return False
        except Exception as e:
            print(e)
            print("errorr")
            self.exception = e
            return False

    def __init__(self, *args, **kwargs):
        super().__init__("Downloading", QgsTask.CanCancel)
        self.key = kwargs.get('mapillary_key')
        self.image_id = kwargs.get('image').get("id")
        self.fields = kwargs.get('fields')


class SignsEditor(QMainWindow, FormClass):
    SUPORTE_TIPO = [
        "Coluna simples",
        "Coluna dupla",
        "Coluna semafórica",
        "Braço projetado",
        "Braço projetado duplo",
        "Semipórtico simples",
        "Semipórtico duplo",
        "Pórtico",
        "Poste Light",
        "Viaduto",
        "Passarela",
        "Outro"
    ]
    key = None
    sign_id = None
    sign_images: list = []
    sign_images_index = -1
    signs_layer: QgsVectorLayer
    roads_layer: QgsVectorLayer
    conf = {}
    placas = None
    code: str = None
    dictionary = {}
    faces = {}
    reloadSign: pyqtSignal = pyqtSignal()
    streetview: str = ""
    mapillary: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.setupUi(self)

    def showEvent(self, event):
        self.connect_signals()
        event.accept()

    def post_init(self, *args, **kwargs):
        self.iface=kwargs.get("iface")
        self.key = kwargs.get('mapillary_key')
        self.conf = kwargs.get('conf')
        self.sign_id = kwargs.get('sign')
        self.taskManager = kwargs.get("task_manager")
        self.sign_images = kwargs.get("sign_images")
        self.sign: QgsFeature = kwargs.get("selected_sign")
        self.signs_layer: QgsVectorLayer = kwargs.get("signs_layer")
        cbx: QComboBox = self.findChild(QComboBox, "suporte")
        cbx.addItem("Selecione...", None)
        for t in self.SUPORTE_TIPO:
            cbx.addItem(t, t)
        cbx.setCurrentIndex(0)
        
        other_but: QPushButton = self.findChild(QPushButton, "brasiltype")
        other_but.clicked.connect(self.select_sign)
        
        self.findChild(QPushButton, "mapillary_url").clicked.connect(self.open_mapillary)
        self.findChild(QPushButton, "streetview_url").clicked.connect(self.open_streetview)
        
        # load mapillary key
        self.mapillary_key = ""
        self.boundary = None
        self.roads_layer: QgsVectorLayer = kwargs.get("roads_layer")
        self.placas = kwargs.get("placas", None)
        self.set_minimap()
        self.spinners()
        
    def open_mapillary(self):       
        QDesktopServices.openUrl(QUrl(self.mapillary))
    
    def open_streetview(self):       
        QDesktopServices.openUrl(QUrl(self.streetview))

    def spinners(self):
        self.findChild(QWebView, "webView").load(
            QUrl(f"file://{os.path.dirname(__file__)}/styles/lg.gif"))

        
    def set_minimap(self):
        canvas: QgsMapCanvas = self.findChild(QgsMapCanvas, "mapview")
        boulder: QgsGeometry = EquidistanceBuffer().buffer(
            self.sign.geometry(
            ), 35, self.signs_layer.crs()
        )

        layer = self.get_point_layer_by_name("popup_sign")
        if layer is not None:
            QgsProject.instance().removeMapLayer(layer)
        layer = QgsVectorLayer('Point?crs=EPSG:4326', 'popup_sign', 'memory')
        layer_data_provider = layer.dataProvider()
        layer_data_provider.addAttributes(self.signs_layer.fields())
        layer_data_provider.addAttributes([QgsField('name', QVariant.String),
                                           QgsField('value', QVariant.Int)])
        layer.updateFields()
        f = QgsFeature()
        f.setGeometry(self.sign.geometry())
        layer.dataProvider().addFeatures([f])
        layer.updateExtents()
        layer.renderer().symbol().setColor(QColor.fromRgb(0, 255, 0))
        QgsProject.instance().addMapLayer(layer)

        canvas.setLayers([layer, self.roads_layer])
        canvas.setExtent(boulder.boundingBox())
        canvas.redrawAllLayers()
        
        if not self.placas:
            with open(os.path.join(os.path.dirname(__file__), "styles/codes_br.txt"), "r") as flu:
                self.placas = [fu[:-1] for fu in flu.readlines()]
                flu.close()
            with open(os.path.join(os.path.dirname(__file__), f"placatype.json"), "r") as flu:
                self.dictionary = json.loads(flu.read())
                flu.close()
            with open(os.path.join(os.path.dirname(__file__), f"placafaces.json"), "r") as flu:
                self.faces = json.loads(flu.read())
                flu.close()
        
        
        self.findChild(QLabel, "mapillary_type_label").setText(self.sign["value"])
        
        self.code = str(self.sign["code"])
        self.face = str(self.sign["face"])
        self.value = str(self.sign["value"])
        
        but = self.findChild(QPushButton, "mapillarytype")
        if os.path.isfile(os.path.join(
            os.path.dirname(__file__), f"styles/symbols/{self.sign.attribute('value')}.svg")):
            but.setIcon(QIcon(os.path.join(
                os.path.dirname(__file__), f"styles/symbols/{self.sign.attribute('value')}.svg")))
        
        self.road_id=None
        if type(self.sign["road"])==int:
            self.road_id = int(self.sign["road"])
            expr = QgsExpression(f'"{self.conf.get("roads_pk")}" = {self.road_id}')
            road: QgsFeature = next(
                self.roads_layer.getFeatures(QgsFeatureRequest(expr)))
            road_name = road[self.conf.get("roads_field_name")]
            self.findChild(QTextEdit, "road_segment").setText(road_name)
        self.findChild(QTextEdit, "text1").setText(self.sign["text1"] or "")
        self.findChild(QTextEdit, "text2").setText(self.sign["text2"] or "")        
        self.findChild(QLineEdit, "face").setText("")
        if self.code != 'NULL':
            self.set_sign(self.code)
            if self.face != 'NULL':
                self.findChild(QLineEdit, "face").setText(self.face)
                self.set_sign_face(self.face)
        else:
            if self.value in self.dictionary:
                self.code = self.dictionary.get(self.value)
                self.face = self.faces.get(self.value, None)
                filename = os.path.join(os.path.dirname(
                    __file__), f"styles/symbols_br/{self.code}.svg")
                if not os.path.isfile(filename):
                    filename = "styles/Question_Mark.svg"
                self.findChild(QPushButton, "brasiltype").setIcon(QIcon(os.path.join(
                    os.path.dirname(__file__), filename)))
                if self.face is not None:
                    if self.face != 'NULL':
                        self.findChild(QLineEdit, "face").setText(self.face)
                        self.set_sign_face(self.face)

        self.findChild(QPushButton, "pushButton_save").clicked.connect(
            lambda: self.save_sign_close())
        self.findChild(QPushButton, "pushButton_next").clicked.connect(
            lambda: self.save_continue())
        self.findChild(QLineEdit, "face").textChanged.connect(
            self.set_sign_face)
        cbx: QComboBox = self.findChild(QComboBox, "suporte")
        cbx.setCurrentIndex(0)
        if self.sign["suporte"] in self.SUPORTE_TIPO:
            cbx.setCurrentIndex(
                1+self.SUPORTE_TIPO.index(self.sign["suporte"]))
        if len(self.sign_images):
            self.sign_images_index = 0
            self.navigate()
        else:
            def go(task, wait_time):
                return self.get_images()
            self.otask = QgsTask.fromFunction(
                'getting images', go, on_finished=self.after_get_images, wait_time=1000)
            QgsApplication.taskManager().addTask(self.otask)
        print("Will set map tool")
        self.set_map_tool()
        
    def after_get_images(self, *args, **kwargs):
        print("AFTER GET IMAGES")
        photos = args[1]
        if "images" in photos:
            self.sign_images_index = 0
            for photo in photos.get("images", {}).get("data", []):
                self.sign_images.append(photo)
            self.navigate()
        
    def get_images(self):
        print("get images")
        url = f'https://graph.mapillary.com/{int(self.sign["id"])}?access_token={self.conf.get("mapillary_key")}&fields=images'
        print(url)
        fu = requests.get(url)
        #    url, headers={'Authorization': "OAuth "+self.conf.get("mapillary_key")})
        if fu.status_code == 200:
            print("got the images")
            photos = fu.json()
            return photos
        print(fu.status_code)
        print("and now")
        return
    
    def save_continue(self):
        print("ooo")
        self.spinners()
        self.save_sign()
        m=self.signs_layer.minimumValue(self.signs_layer.fields().indexOf('certain')) 
        expr = QgsExpression( f"\"saved\" is null and \"certain\" is not null and \"certain\" > 0")  
        req=QgsFeatureRequest(expr)
        fids=[(f["certain"],f.id()) for f in self.signs_layer.getFeatures(req)]
        fids.sort()
        self.sign=self.signs_layer.getFeature(fids[0][1])
        self.sign_id=fids[0][1]
        self.sign_images=[]
        def go(task, wait_time):
            print("go get the imagery")
            return self.get_images()
        self.otask = QgsTask.fromFunction(
            'getting images', go, on_finished=self.after_get_images, wait_time=1000)
        QgsApplication.taskManager().addTask(self.otask)
        self.set_minimap()
        
    
    def save_sign_close(self):
        self.save_sign()
        self.reloadSign.emit()
        self.close()

    def save_sign(self):
        is_correct = self.findChild(
            QCheckBox, "correctly_identified").isChecked()
        if self.code is not None:
            self.signs_layer.startEditing()
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("code"), self.code)
            if self.face is not None:
                self.signs_layer.changeAttributeValue(
                    self.sign.id(), self.sign.fieldNameIndex("face"), self.face)
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("text1"), self.findChild(QTextEdit, "text1").toPlainText())
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("text2"), self.findChild(QTextEdit, "text2").toPlainText())
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("suporte"), self.findChild(QComboBox, "suporte").currentText())
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("saved"),True)

            self.signs_layer.commitChanges()
        if is_correct:
            dictionary = {}
            faces = {}
            if os.path.isfile(os.path.join(os.path.dirname(__file__), f"placatype.json")):
                with open(os.path.join(os.path.dirname(__file__), f"placatype.json"), "r") as fu:
                    dictionary = json.loads(fu.read())
                fu.close()
            if os.path.isfile(os.path.join(os.path.dirname(__file__), f"placafaces.json")):
                with open(os.path.join(os.path.dirname(__file__), f"placafaces.json"), "r") as fu:
                    faces = json.loads(fu.read())
                fu.close()
            self.dictionary[self.sign["value"]] = self.code
            self.faces[self.sign["value"]] = self.face
            with open(os.path.join(os.path.dirname(__file__), f"placatype.json"), "w") as fu:
                fu.write(json.dumps(self.dictionary))
            with open(os.path.join(os.path.dirname(__file__), f"placafaces.json"), "w") as fu:
                fu.write(json.dumps(self.faces))

    def select_sign(self):
        fu = PlacaSelector(placas=self.placas)
        fu.applyClicked.connect(self.set_sign)
        fu.exec()

    def set_sign(self, *args, **kwargs):
        print(os.path.join(
            os.path.dirname(__file__), f"styles/symbols_br/{args[0]}.svg"))
        self.findChild(QPushButton, "brasiltype").setIcon(QIcon(os.path.join(
            os.path.dirname(__file__), f"styles/symbols_br/{args[0]}.svg")))
        self.findChild(QTextEdit, "code_text").setText(args[0])
        self.code = args[0]

    def set_sign_face(self, *args, **kwargs):
        self.face = args[0]
        if self.code is None:
            return
        if not os.path.isfile(os.path.join(
                os.path.dirname(__file__), f"styles/symbols_br/{self.code}.svg")):
            return
        with open(os.path.join(
                os.path.dirname(__file__), f"styles/symbols_br/{self.code}.svg")) as fu:
            svg = fu.read()
        fu.close()
        if self.code=="R-15":
            svg = svg.replace(
                "</svg>", f'<text x="400" y="470" font-size="200" fill="black" text-anchor="middle" font-family="sans-serif">{self.face}</text></svg>')
        elif self.code=="R-19":
            svg = svg.replace(
                "</svg>", f'<text x="400" y="500" font-size="400" fill="black" text-anchor="middle" font-family="sans-serif">{self.face}</text></svg>')
        else:    
            svg = svg.replace(
                "</svg>", f'<text x="400" y="500" font-size="400" fill="black" text-anchor="middle" font-family="sans-serif">{self.face}</text></svg>')
        with open(os.path.join(
                os.path.dirname(__file__), f"styles/symbols_br_faced/{self.code}-{self.face}.svg"), "w") as fu:
            svg = fu.write(svg)
        fu.close()
        self.findChild(QPushButton, "brasiltype").setIcon(QIcon(os.path.join(
            os.path.dirname(__file__), f"styles/symbols_br_faced/{self.code}-{self.face}.svg")))

    def forward(self, *args, **kwargs):
        print("FORWARDSS")
        self.sign_images_index += 1
        self.sign_images_index = self.sign_images_index % len(self.sign_images)
        self.navigate()

    def navigate(self):
        print("navidage")
        self.dl = SignDataDownloader(
            mapillary_key=self.key, image=self.sign_images[self.sign_images_index], fields='thumb_1024_url,computed_compass_angle,computed_geometry,captured_at,detections')
        self.dl.taskCompleted.connect(self.show_image)
        QgsApplication.taskManager().addTask(self.dl)

    def backward(self):
        self.sign_images_index -= 1
        if self.sign_images_index < 0:
            self.sign_images_index = len(self.sign_images)-1
        self.navigate()

    def connect_signals(self):
        print("will connect signals")
        self.findChild(
            QPushButton, "pushButton_cancel").clicked.connect(self.close)
        self.findChild(QPushButton, "pushButton_forward").clicked.connect(
            self.forward)
        self.findChild(QPushButton, "pushButton_back").clicked.connect(
            self.backward)

    def get_point_layer_by_name(self, name):
        layers = list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [QgsWkbTypes.Point, QgsWkbTypes.MultiPoint] and x.name(
        ) == name, QgsProject.instance().mapLayers().values()))
        if layers:
            return layers[0]

    def show_image(self, *args, **kwargs):
        g=self.dl.result.get("computed_geometry").get("coordinates")
        print("GOT TH E EEOMAA")
        print(self.dl.result)
        #{'thumb_1024_url': 'https://z-p3-scontent.fcgh5-1.fna.fbcdn.net/m1/v/t6/An_aOEAhNXXB1sd4jG1DE9WFg8fKVglC5qq9b-9we9YWasrWq5-6utjvQJy8CEtZY3mVhCNLMZm1VXZgDdQvLpRO2dU1vRwtqowTN-2IP2fEeeE_rbCaZAXN2KYgg7r98XaqYjJ3jpdSN2VlJBNbCQ?stp=s1024x768&ccb=10-5&oh=00_AYD823tB-x3M4fhKciP3uPY5EdfsS2sM58W8sGyUEg4CUg&oe=66C89D46&_nc_sid=201bca&_nc_zt=28', 'computed_compass_angle': 60.289959149676, 'computed_geometry': {'type': 'Point', 'coordinates': [-43.371146739942, -22.92186299989]}, 'captured_at': 1563902953000, 'id': '178986934111182'}

        self.streetview=f"http://maps.google.com/maps?q=&layer=c&cbll={g[1]},{g[0]}"
        self.mapillary=f"https://www.mapillary.com/app/?lat={g[1]}&lng={g[0]}&z=17&pKey={self.dl.result.get('id')}"
        arrows_layer = self.get_point_layer_by_name("arrows_popup_layer")
        canvas: QgsMapCanvas = self.findChild(QgsMapCanvas, "mapview")
        if arrows_layer is None:
            arrows_layer = QgsVectorLayer(
                'Point?crs=EPSG:4326', 'arrows_popup_layer', 'memory')
            arrows_layer.dataProvider().addAttributes([QgsField('id', QVariant.String),
                                                       QgsField('compass', QVariant.Double)])
            QgsProject.instance().addMapLayer(arrows_layer)
        if self.dl.result is None:
            print("No result?")
            return
        dt = datetime.datetime.fromtimestamp(
            0.001*self.dl.result.get("captured_at"))
        # str(self.dl.result.get("captured_at")))
        self.findChild(QLabel, "date").setText(
            dt.strftime("%m/%d/%Y, %H:%M:%S"))
        fu = QgsFeature()
        fu.setAttributes(
            [self.dl.result.get("id"), self.dl.result.get("computed_compass_angle")])
        fu.setGeometry(QgsGeometry.fromPoint(
            QgsPoint(*self.dl.result.get("computed_geometry").get("coordinates"))))
        svg_path = os.path.join(os.path.dirname(__file__), f"styles/arrow.svg")
        svg_marker = QgsSvgMarkerSymbolLayer(svg_path)
        svg_marker.setAngle(self.dl.result.get("computed_compass_angle"))
        svg_marker.setSize(8)

        # Create a marker symbol and add the SVG marker to it
        symbol = QgsMarkerSymbol.createSimple({})
        symbol.changeSymbolLayer(0, svg_marker)

        # Apply the symbol to the layer's renderer
        arrows_layer.renderer().setSymbol(symbol)

        arrows_layer.dataProvider().truncate()
        arrows_layer.dataProvider().addFeatures([fu])
        arrows_layer.updateExtents()
        l = canvas.layers()
        l.append(arrows_layer)
        canvas.setLayers(l)
        canvas.redrawAllLayers()
        self.findChild(QWebView, "webView").load(
            QUrl(self.dl.result.get("thumb_1024_url")))
        #https://graph.mapillary.com/:image_id/detections
        
    def set_map_tool(self):
        print("setting map toool")  
        canvas: QgsMapCanvas = self.findChild(QgsMapCanvas, "mapview")

        self.mapTool = RoadsSelector(canvas, self.roads_layer)
        self.mapTool.geomIdentified.connect(self.display_road)
        self.mapTool.setLayer(self.roads_layer)
        canvas: QgsMapCanvas = self.findChild(QgsMapCanvas, "mapview")
        canvas.setMapTool(self.mapTool)
        print("set the tool")
        
    def display_road(self, *args, **kwargs):
        print("display the road now")
        self.road_id=args[1][self.conf.get("roads_pk")]
        print(self.road_id)
        road_name=args[1][self.conf.get("roads_field_name")]
        self.findChild(QTextEdit, "road_segment").setText(road_name)

        print(args)