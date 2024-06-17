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
from qgis.PyQt.QtGui import QTransform
from .placa_selector import PlacaSelector


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

    def __init__(self, *args, **kwargs):
        super().__init__(parent=kwargs.get("parent"))

        self.setWindowTitle("Signs Editor")
        self.setupUi(self)
        self.connect_signals()
        self.key = kwargs.get('mapillary_key')
        self.sign_id = kwargs.get('sign')
        self.sign_images = kwargs.get("sign_images")
        self.sign: QgsFeature = kwargs.get("selected_sign")
        self.signs_layer = kwargs.get("signs_layer")

        but = self.findChild(QPushButton, "mapillarytype")
        but.setIcon(QIcon(os.path.join(
            os.path.dirname(__file__), f"styles/symbols/{self.sign.attribute('value')}.svg")))

        other_but: QPushButton = self.findChild(QPushButton, "brasiltype")
        print(other_but)
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
        canvas.setLayers([roads])
        canvas.setExtent(boulder.boundingBox())
        canvas.redrawAllLayers()

        if self.sign_images:
            self.sign_images_index = 0
            self.navigate()
        self.placas = kwargs.get("placas", None)
        if not self.placas:
            self.placas = [
                fu[:-1] for fu in open(os.path.join(os.path.dirname(__file__), "styles/codes_br.txt"), "r")]
        self.dictionary = json.loads(
            open(os.path.join(os.path.dirname(__file__), f"placatype.json"), "r").read())
        if self.sign["value"] in self.dictionary:
            filename=f"styles/symbols_br/{self.dictionary.get(self.sign['value'])}.svg"
            if not os.path.isfile(filename):
                filename="styles/Question_Mark.svg"
            self.findChild(QPushButton, "brasiltype").setIcon(QIcon(os.path.join(
                os.path.dirname(__file__), filename)))

                

        self.findChild(QPushButton, "pushButton_save").clicked.connect(
            self.save_sign)

    def save_sign(self):
        is_correct = self.findChild(
            QCheckBox, "correctly_identified").isChecked()
        if self.code is not None:
            self.signs_layer.startEditing()
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("code"), self.code)
            self.signs_layer.commitChanges()
        if is_correct:
            dictionary = json.loads(
                open(os.path.join(os.path.dirname(__file__), f"placatype.json"), "r").read())
            dictionary[self.sign["value"]] = self.code
            with open(os.path.join(os.path.dirname(__file__), f"placatype.json"), "w") as fu:
                fu.write(json.dumps(dictionary))
            v = self.sign["value"]
            print(v)
            print(dictionary)

        print("saving", is_correct)
        self.close()

    def select_sign(self):
        fu = PlacaSelector(placas=self.placas)
        fu.applyClicked.connect(self.set_sign)
        fu.exec()

    def set_sign(self, *args, **kwargs):
        print("ACKnowledge", args)
        self.findChild(QPushButton, "brasiltype").setIcon(QIcon(os.path.join(
            os.path.dirname(__file__), f"styles/symbols_br/{args[0]}.svg")))
        self.code = args[0]
        print("THE FEATURE ID IS ", self.sign.id())
        print("WIIWLKIWLKWILWIW", kwargs)

    def forward(self):
        self.sign_images_index += 1
        self.sign_images_index = self.sign_images_index % len(self.sign_images)
        self.navigate()

    def navigate(self):
        self.dl = SignDataDownloader(
            mapillary_key=self.key, image=self.sign_images[self.sign_images_index], fields='thumb_1024_url')
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

    def show_image(self, *args, **kwargs):
        self.findChild(QWebView, "webView").load(
            QUrl(self.dl.result.get("thumb_1024_url")))
