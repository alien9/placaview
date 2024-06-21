from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal, QUrl, QSize
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget, QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit,  QFormLayout,  QHBoxLayout, QGraphicsView, QVBoxLayout, QApplication, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from qgis.PyQt import uic
from qgis.PyQt.QtSvg import QGraphicsSvgItem, QSvgRenderer, QSvgWidget
import qgis.PyQt.QtSvg
from qgis.PyQt.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from qgis.PyQt.QtSvg import QSvgWidget, QSvgRenderer
from qgis.PyQt.QtGui import QTransform, QColor
from .placa_selector import PlacaSelector
from qgis.core import *

from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsTask)
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.gui import QgsMapCanvas
from .equidistance_buffer import EquidistanceBuffer
from qgis.gui import QgsFilterLineEdit
import os
import requests
import re
import json
from .signs_filter_item import SignsFilterItem

FormClass, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'signs_editor.ui'))


class SignDataDownloader(QgsTask):
    key = None
    image_id = None
    result = None

    def run(self):
        r = requests.get(
            f"https://graph.mapillary.com/{self.image_id}?access_token={self.key}&fields={self.fields}")
        if r.status_code == 200:
            self.result = r.json()
            return True
        return

    def __init__(self, *args, **kwargs):
        super().__init__("Downloading", QgsTask.CanCancel)
        self.key = kwargs.get('mapillary_key')
        self.image_id = kwargs.get('image').get("id")
        self.fields = kwargs.get('fields')


class SignsEditor(QDialog, FormClass):
    key = None
    sign_id = None
    sign_images: list = []
    sign_images_index = -1
    signs_layer: QgsVectorLayer
    placas = None
    code: str = None
    dictionary = {}
    faces = {}

    def __init__(self, *args, **kwargs):
        super().__init__(parent=kwargs.get("parent"))

        self.setWindowTitle("Signs Editor")
        self.setupUi(self)
        self.connect_signals()
        self.key = kwargs.get('mapillary_key')
        self.sign_id = kwargs.get('sign')
        self.sign_images = kwargs.get("sign_images")
        self.sign: QgsFeature = kwargs.get("selected_sign")
        self.signs_layer: QgsVectorLayer = kwargs.get("signs_layer")

        but = self.findChild(QPushButton, "mapillarytype")
        but.setIcon(QIcon(os.path.join(
            os.path.dirname(__file__), f"styles/symbols/{self.sign.attribute('value')}.svg")))

        other_but: QPushButton = self.findChild(QPushButton, "brasiltype")
        other_but.clicked.connect(self.select_sign)

        # print("bugado")
        # print(self.sign.attributes()[self.sign.fieldNameIndex("code")])
        # print(self.sign.fieldNameIndex("code"))
        # if self.sign.attributes()[self.sign.fieldNameIndex("code")]:
        #    print("Existe sim")
        # if QVariant.isNull(self.sign.attributes()[self.sign.fieldNameIndex("code")]):
        #    print("nao sei meishmo")

        # load mapillary key
        self.mapillary_key = ""
        self.boundary = None
        self.roads_layer = None
        self.conf = {}

        canvas: QgsMapCanvas = self.findChild(QgsMapCanvas, "mapview")

        boulder: QgsGeometry = EquidistanceBuffer().buffer(
            kwargs.get("selected_sign").geometry(
            ), 35, kwargs.get('signs_layer').crs()
        )
        roads: QgsVectorLayer = kwargs.get("roads")
        layer = QgsVectorLayer('Point?crs=EPSG:4326', 'popup_sign', 'memory')
        canvas.setLayers([roads, layer])
        if not layer.isValid():
            print("Layer creation failed!")
        layer.startEditing()
        # Define fields for the layer
        layer_data_provider = layer.dataProvider()
        #layer_data_provider.addAttributes(self.signs_layer.fields())
        layer_data_provider.addAttributes([QgsField('name', QVariant.String),
                                        QgsField('value', QVariant.Int)])
        layer.updateFields()
        print("WILL ADD THE FARARAR")
        print(self.sign)
        print(self.sign.geometry())

        #layer.commitChanges()
        f=QgsFeature()
        f.setGeometry(self.sign.geometry())
        f.setAttributes(['peganingas', 1])
        print("adding")
        print(self.sign.geometry())
        layer.dataProvider().addFeatures([f])
        layer.updateExtents()
        layer.renderer().symbol().setColor(QColor.fromRgb( 0, 255, 0))
        
        #layer.addFeatures([self.sign])
        
        layer.commitChanges()

        print(layer.extent().xMaximum())
        QgsProject.instance().addMapLayer(layer)
        canvas.setLayers([roads, layer])
        canvas.setExtent(boulder.boundingBox())
        canvas.redrawAllLayers()

        if self.sign_images:
            self.sign_images_index = 0
            self.navigate()
        self.placas = kwargs.get("placas", None)
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
        self.code = str(self.sign["code"])
        self.face = str(self.sign["face"])
        self.value= str(self.sign["value"])
        if self.code != 'NULL':
            self.set_sign(self.code)
            if self.face != 'NULL':
                self.findChild(QLineEdit, "face").setText(self.face)
                self.set_sign_face(self.face)
        else:
            if self.value in self.dictionary:
                self.code=self.dictionary.get(self.value)
                self.face=self.faces.get(self.value, None)
                filename = os.path.join(os.path.dirname(__file__),f"styles/symbols_br/{self.code}.svg")
                if not os.path.isfile(filename):
                    filename = "styles/Question_Mark.svg"
                self.findChild(QPushButton, "brasiltype").setIcon(QIcon(os.path.join(
                    os.path.dirname(__file__), filename)))
                if self.face is not None:
                    if self.face != 'NULL':
                        self.findChild(QLineEdit, "face").setText(self.face)
                        self.set_sign_face(self.face)

        self.findChild(QPushButton, "pushButton_save").clicked.connect(
            self.save_sign)
        self.findChild(QLineEdit, "face").textChanged.connect(
            self.set_sign_face)

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

        self.close()

    def select_sign(self):
        fu = PlacaSelector(placas=self.placas)
        fu.applyClicked.connect(self.set_sign)
        fu.exec()

    def set_sign(self, *args, **kwargs):
        print(os.path.join(
            os.path.dirname(__file__), f"styles/symbols_br/{args[0]}.svg"))
        self.findChild(QPushButton, "brasiltype").setIcon(QIcon(os.path.join(
            os.path.dirname(__file__), f"styles/symbols_br/{args[0]}.svg")))
        self.code = args[0]

    def set_sign_face(self, *args, **kwargs):
        self.face = args[0]
        if self.code is None:
            return
        with open(os.path.join(
                os.path.dirname(__file__), f"styles/symbols_br/{self.code}.svg")) as fu:
            svg = fu.read()
        fu.close()
        svg = svg.replace(
            "</svg>", f'<text x="400" y="500" font-size="400" fill="black" text-anchor="middle" font-family="sans-serif">{self.face}</text></svg>')
        with open(os.path.join(
                os.path.dirname(__file__), f"styles/symbols_br_faced/{self.code}-{self.face}.svg"), "w") as fu:
            svg = fu.write(svg)
        fu.close()
        self.findChild(QPushButton, "brasiltype").setIcon(QIcon(os.path.join(
            os.path.dirname(__file__), f"styles/symbols_br_faced/{self.code}-{self.face}.svg")))

    def forward(self):
        self.sign_images_index += 1
        self.sign_images_index = self.sign_images_index % len(self.sign_images)
        self.navigate()

    def navigate(self):
        self.dl = SignDataDownloader(
            mapillary_key=self.key, image=self.sign_images[self.sign_images_index], fields='thumb_1024_url,computed_compass_angle,computed_geometry')
        self.dl.taskCompleted.connect(self.show_image)
        QgsApplication.taskManager().addTask(self.dl)

    def backward(self):
        self.sign_images_index -= 1
        if self.sign_images_index < 0:
            self.sign_images_index = len(self.sign_images)-1
        self.navigate()

    def connect_signals(self):
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
        print(self.dl.result)
        arrows_layer=self.get_point_layer_by_name("arrows_popup_layer")
        canvas: QgsMapCanvas = self.findChild(QgsMapCanvas, "mapview")
        if arrows_layer is None:
            arrows_layer= QgsVectorLayer('Point?crs=EPSG:4326', 'arrows_popup_layer', 'memory')
            arrows_layer.dataProvider().addAttributes([QgsField('id', QVariant.String),
                                        QgsField('compass', QVariant.Double)])
            QgsProject.instance().addMapLayer(arrows_layer)
            l=canvas.layers()
            l.append(arrows_layer)
            canvas.setLayers(l)
        fu=QgsFeature()
        fu.setAttributes([self.dl.result.get("id"),self.dl.result.get("computed_compass_angle")])
        fu.setGeometry(QgsGeometry.fromPoint(QgsPoint(*self.dl.result.get("computed_geometry").get("coordinates"))))
        svg_path = os.path.join(os.path.dirname(__file__), f"styles/arrow.svg")
        # Replace with the path to your SVG file
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
        
        
        canvas.redrawAllLayers()
        self.findChild(QWebView, "webView").load(
            QUrl(self.dl.result.get("thumb_1024_url")))
