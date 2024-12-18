from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject, QgsApplication
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal, QUrl, QSize
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDesktopWidget, QWidget, QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox, QComboBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit, QCompleter, QTextEdit,  QFormLayout,  QHBoxLayout, QGraphicsView, QVBoxLayout, QApplication, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from qgis.PyQt import uic
from qgis.PyQt.QtSvg import QGraphicsSvgItem, QSvgRenderer, QSvgWidget
import qgis.PyQt.QtSvg
from qgis.PyQt.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGridLayout
from qgis.PyQt.QtSvg import QSvgWidget, QSvgRenderer
from qgis.PyQt.QtGui import QTransform, QColor, QPolygon, QPainter
from .placa_selector import PlacaSelector
from qgis.core import *
from qgis.PyQt.QtCore import pyqtSignal, QPoint, QRectF
from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsTask)
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.gui import QgsMapCanvas, QgsMapToolIdentifyFeature
from .equidistance_buffer import EquidistanceBuffer
from qgis.gui import QgsFilterLineEdit
from qgis.core import NULL
import os
import requests
import re
import json
import shutil
import datetime
from .roads_selector import RoadsSelector

FormClass, eck = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'signs_editor.ui'))


class DetectionCanvas(QWidget):
    rect = []

    def __init__(self):
        super().__init__()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(255, 0, 255, 255))
        if self.rect:
            for r, s in self.rect:
                painter.drawRect(*r)
                painter.drawText(QPoint(r[0], r[1]), s)

    def reset_canvas(self):
        self.rect = []
        self.repaint()

    def draw_rectangle(self, rect, text):
        self.rect.append((rect, text))
        self.repaint()


class SignDataDownloader(QgsTask):
    key = None
    image_id = None
    result = None
    road_id: int = None
    road_name: str = None
    datatype: str = "imagery"

    def run(self):
        try:
            if self.datatype == "imagery":
                url = f"https://graph.mapillary.com/{self.image_id}?access_token={self.key}&fields={self.fields}"
            if self.datatype == "geometry":
                url = f'https://graph.mapillary.com/{self.image_id}/detections?access_token={self.key}&fields=geometry,value'
            r = requests.get(url)
            if r.status_code == 200:
                self.result = r.json()
                return True
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
        if "datatype" in kwargs:
            self.datatype = kwargs.get("datatype")


class SignsEditor(QMainWindow, FormClass):
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
    filter: list = []
    canvas: DetectionCanvas = None
    viewing_index: int = 0

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.signs_layer: QgsVectorLayer = kwargs.get("signs_layer")
        self.filter = kwargs.get("filter")
        self.setupUi(self)
        edits = self.findChildren(QLineEdit)
        for f in edits:
            field_name = f.objectName()
            auto_complete_values = self.read_autocomplete(field_name)
            if auto_complete_values:
                completer = QCompleter(auto_complete_values, self)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                f.setCompleter(completer)
        print("sdone ir up")

    def check_path(self):
        patty = QgsProject.instance().readPath("./")
        print(QgsProject.instance().fileName())
        if not patty:
            return False
        if not os.path.isdir(f"{QgsProject.instance().fileName()}_data"):
            os.mkdir(f"{QgsProject.instance().fileName()}_data")
        if not os.path.isdir(f"{QgsProject.instance().fileName()}_data/autocomplete"):
            os.mkdir(f"{QgsProject.instance().fileName()}_data/autocomplete")
        return True

    def read_autocomplete(self, field_name):
        wordList = []
        if not self.check_path():
            return
        patty = f'{QgsProject.instance().fileName()}_data/autocomplete'
        if os.path.isfile(f"{os.path.dirname(__file__)}/styles/autocomplete/{field_name}.txt"):
            if not os.path.isfile(f"{patty}/{field_name}.txt"):
                shutil.copy(
                    f"{os.path.dirname(__file__)}/styles/autocomplete/{field_name}.txt", f"{patty}/{field_name}.txt")
        if os.path.isfile(f"{patty}/{field_name}.txt"):
            with open(f"{patty}/{field_name}.txt") as fu:
                wordList = set([" "+line.rstrip()+" " for line in fu.readlines()])
            fu.close()
            if len(field_name) > 6:
                fname = str.replace(field_name, "text", "")
            else:
                fname=field_name
            idx = self.signs_layer.fields().indexOf(fname)
            values = self.signs_layer.uniqueValues(idx)
            for v in values:
                palabra=" "+str(v)+" "
                if len(palabra)>2 and palabra!=" NULL ":
                    wordList.add(palabra)
            return sorted(list(wordList))

    def write_autocomplete(self, field_name, values):
        if not self.check_path():
            return
        patty = f'{QgsProject.instance().fileName()}_data/autocomplete'
        with open(f"{patty}/{field_name}.txt", "w+") as fu:
            for v in list(set(values)):
                fu.write(f"{v}\n")
            fu.close()
        completer = QCompleter(values, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.findChild(QLineEdit, field_name).setCompleter(completer)

    def set_fields_autocomplete(self):
        edits = self.findChildren(QLineEdit)
        patty = f'{QgsProject.instance().fileName()}_data/autocomplete'
        for f in edits:
            field_name = f.objectName()
            auto_complete_values = self.read_autocomplete(field_name)
            if auto_complete_values:
                completer = QCompleter(auto_complete_values, self)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                f.setCompleter(completer)

    def post_init(self, *args, **kwargs):
        self.iface = kwargs.get("iface")
        self.key = kwargs.get('mapillary_key')
        self.conf = kwargs.get('conf')
        self.sign_id = kwargs.get('sign')
        self.sign_images = kwargs.get("sign_images")
        if "selected_sign" in kwargs:
            self.sign: QgsFeature = kwargs.get("selected_sign")
        else:
            self.load_next_record()
        self.signs_layer: QgsVectorLayer = kwargs.get("signs_layer")
        self.filter = kwargs.get("filter")
        other_but: QPushButton = self.findChild(QPushButton, "brasiltype")
        other_but.clicked.connect(self.select_sign)

        self.findChild(QPushButton, "mapillary_url").clicked.connect(
            self.open_mapillary)
        self.findChild(QPushButton, "streetview_url").clicked.connect(
            self.open_streetview)

        # load mapillary key
        self.mapillary_key = ""
        self.boundary = None
        self.roads_layer: QgsVectorLayer = kwargs.get("roads_layer")
        self.placas = kwargs.get("placas", None)
        self.set_minimap()
        self.spinners()
        self.organize()
        self.findChild(QPushButton, "pushButton_save").clicked.connect(
            lambda: self.save_sign_close())
        self.findChild(QPushButton, "pushButton_next").clicked.connect(
            lambda: self.save_continue())
        self.findChild(QPushButton, "pushButton_next_no_save").clicked.connect(
            lambda: self.avancate())
        self.findChild(QLineEdit, "face").textChanged.connect(
            self.set_sign_face)
        self.open_record()
        self.connect_signals()

    def avancate(self):
        self.viewing_index += 1
        self.load_next_record()

    def get_canvas(self):
        if self.canvas is None:
            self.canvas = DetectionCanvas()
            grid: QGridLayout = self.findChild(QGridLayout, "web_grid_layout")
            grid.addWidget(self.canvas, 0, 0, Qt.AlignCenter)
        return self.canvas

    def organize(self):
        g = QDesktopWidget().availableGeometry()
        fu = self.findChild(QWebView, "webView")
        fu.setFixedWidth(g.width()-370)
        fu.setFixedHeight(g.height()-120)
        canvas = self.get_canvas()
        canvas.setFixedWidth(g.width()-370)
        canvas.setFixedHeight(g.height()-120)
        canvas.setStyleSheet("background-color:black;")

    def open_mapillary(self):
        QDesktopServices.openUrl(QUrl(self.mapillary))

    def open_streetview(self):
        QDesktopServices.openUrl(QUrl(self.streetview))

    def spinners(self):
        self.findChild(QWebView, "webView").load(
            QUrl(f"file://{os.path.dirname(__file__)}/styles/lg.gif"))

    def set_minimap(self):
        if not self.sign:
            self.load_next_record()
            return
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

        self.findChild(QLabel, "mapillary_type_label").setText(
            self.sign["value"])

        self.code = str(self.sign["code"])
        self.face = str(self.sign["face"])
        self.value = str(self.sign["value"])

        but = self.findChild(QPushButton, "mapillarytype")
        if os.path.isfile(os.path.join(
                os.path.dirname(__file__), f"styles/symbols/{self.sign.attribute('value')}.svg")):
            but.setIcon(QIcon(os.path.join(
                os.path.dirname(__file__), f"styles/symbols/{self.sign.attribute('value')}.svg")))

        self.road_id = None
        print("loading road")
        if type(self.sign["road"]) == int:
            self.road_id = int(self.sign["road"])
            expr = QgsExpression(
                f'"{self.conf.get("roads_pk")}" = {self.road_id}')
            road:QgsFeature=None
            for co in self.roads_layer.getFeatures(QgsFeatureRequest(expr)):
                road=co
            #road: QgsFeature = next(
                #self.roads_layer.getFeatures(QgsFeatureRequest(expr)))
                road_name = road[self.conf.get("roads_field_name")]
                self.findChild(QTextEdit, "road_segment").setText(road_name)
        self.findChild(QLineEdit, "text1").setText(self.sign["text1"] or "")
        self.findChild(QLineEdit, "text2").setText(self.sign["text2"] or "")
        self.findChild(QLineEdit, "textsuporte").setText(
            self.sign["suporte"] or "")
        self.findChild(QLineEdit, "face").setText(self.sign["face"] or "")
        self.findChild(QTextEdit, "observations").setText(self.sign["observations"] or "")
        self.findChild(QLineEdit, "sign_id_edit").setText(str(int(self.sign["id"])) or "")
        self.findChild(QLineEdit, "sign_id_edit").setReadOnly(True)
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

        # cbx: QComboBox = self.findChild(QComboBox, "suporte")
        # cbx.setCurrentIndex(0)
        # if self.sign["suporte"] in self.SUPORTE_TIPO:
        #    cbx.setCurrentIndex(
        #        1+self.SUPORTE_TIPO.index(self.sign["suporte"]))
        if len(self.sign_images):
            self.sign_images_index = 0
            self.navigate()
        else:
            def go(task, wait_time):
                return self.get_images()
            self.otask = QgsTask.fromFunction(
                'getting images', go, on_finished=self.after_get_images, wait_time=1000)
            QgsApplication.taskManager().addTask(self.otask)
        self.set_map_tool()

    def after_get_images(self, *args, **kwargs):
        self.sign_images = []
        photos = args[1]
        if "images" in photos:
            self.sign_images_index = 0
            for photo in photos.get("images", {}).get("data", []):
                self.sign_images.append(photo)
            self.navigate()
            self.set_minimap()

    def get_images(self):
        url = f'https://graph.mapillary.com/{int(self.sign["id"])}?access_token={self.conf.get("mapillary_key")}&fields=images'
        print(url)
        fu = requests.get(url)
        #    url, headers={'Authorization': "OAuth "+self.conf.get("mapillary_key")})
        if fu.status_code == 200:
            photos = fu.json()
            return photos
        return

    def save_continue(self):
        self.spinners()
        self.save_sign()
        self.close_record()
        self.load_next_record()

    def open_record(self):
        if not self.sign:
            return
        self.signs_layer.startEditing()
        self.signs_layer.changeAttributeValue(
            self.sign.id(), self.sign.fieldNameIndex("opened"), os.getenv("USERNAME"))
        self.signs_layer.commitChanges()

    def close_record(self):
        if not self.sign:
            return
        self.signs_layer.startEditing()
        self.signs_layer.changeAttributeValue(
            self.sign.id(), self.sign.fieldNameIndex("opened"), None)
        self.signs_layer.commitChanges()

    def load_next_record(self):
        geo=None
        if self.sign:
            geo=QgsPointXY(self.sign.geometry().constGet())
        self.reset_form()
        if not self.signs_layer:
            return
        m = self.signs_layer.minimumValue(
            self.signs_layer.fields().indexOf('certain'))
        distance = QgsDistanceArea()
        expr = QgsExpression(
            f"\"saved\" is null and \"certain\" is not null and \"certain\" > 0 and opened is null and \"status\" is null ")
        req = QgsFeatureRequest(expr)
        if geo:
            fids = sorted([(f["certain"], f.id(), f["value_code_face"], distance.measureLine(geo, QgsPointXY(f.geometry().constGet())))
                    for f in list(filter(lambda x: x["value_code_face"] in self.filter, self.signs_layer.getFeatures(req)))], key=lambda a: a[3])
            #fids = [(f["certain"], f.id(), f["value_code_face"], distance.measureLine(geo, QgsPointXY(f.geometry().constGet())))
            #        for f in list(filter(lambda x: x["value_code_face"] in self.filter, self.signs_layer.getFeatures(req)))]
        else:
            fids = [(f["certain"], f.id(), f["value_code_face"], 0)
                    for f in list(filter(lambda x: x["value_code_face"] in self.filter, self.signs_layer.getFeatures(req)))]
        if len(fids) == 0:
            expr = QgsExpression(
                f"\"saved\" is null and opened is null and \"status\" is null ")
            req = QgsFeatureRequest(expr)
            fids = [(f["certain"], f.id(), f["value_code_face"])
                    for f in self.signs_layer.getFeatures(req)]
            fids = list(filter(lambda x: x[2] in self.filter, fids))
        if len(fids) > 0:
            found_index = self.viewing_index % len(fids)
            self.sign = self.signs_layer.getFeature(fids[found_index][1])
            self.open_record()
            self.sign_id = fids[found_index][1]
            self.sign_images = []

            def go(task, wait_time):
                return self.get_images()
            self.otask = QgsTask.fromFunction(
                'getting images', go, on_finished=self.after_get_images, wait_time=1000)
            QgsApplication.taskManager().addTask(self.otask)
            self.set_minimap()
        else:
            dlsg = QMessageBox(self)
            dlsg.setText("There are no signs to edit")
            dlsg.exec()
            self.close()

    def reset_form(self):
        self.findChild(QCheckBox, "not_a_sign").setChecked(False)
        self.findChild(QCheckBox, "remember2").setChecked(False)
        self.findChild(QCheckBox, "remember1").setChecked(False)
        self.findChild(QCheckBox, "remembersuporte").setChecked(False)
        self.findChild(QCheckBox, "correctly_identified").setChecked(False)
        self.findChild(QTextEdit, "code_text").setText("")
        self.findChild(QLineEdit, "textsuporte").setText("")
        self.findChild(QLineEdit, "text1").setText("")
        self.findChild(QLineEdit, "text2").setText("")
        self.findChild(QLineEdit, "sign_id_edit").setText("")
        self.findChild(QLineEdit, "sign_id_edit").setReadOnly(True)

    def save_sign_close(self):
        self.save_sign()
        self.close_record()
        self.reloadSign.emit()
        self.close()

    def save_sign(self):
        is_correct = self.findChild(
            QCheckBox, "correctly_identified").isChecked()
        is_not_a_sign = self.findChild(
            QCheckBox, "not_a_sign").isChecked()
        face = self.findChild(QLineEdit, "face").text()
        if self.code is not None:
            self.signs_layer.startEditing()
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("code"), self.code)
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("road"), self.road_id)
            vcf = self.code
            if face != '':  
                self.signs_layer.changeAttributeValue(
                    self.sign.id(), self.sign.fieldNameIndex("face"), face)
                placa_style = f"symbols_br_faced/{vcf}-{face}.svg"
                self.signs_layer.changeAttributeValue(
                    self.sign.id(), self.sign.fieldNameIndex("value_code_face"), placa_style)
            else:
                placa_style = f"symbols_br/{vcf}.svg"
                self.signs_layer.changeAttributeValue(
                    self.sign.id(), self.sign.fieldNameIndex("value_code_face"), placa_style)

            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("text1"), re.sub("^\\s|\\s*$", "", self.findChild(QLineEdit, "text1").text()))
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("text2"), re.sub("^\\s|\\s*$", "", self.findChild(QLineEdit, "text2").text()))
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("suporte"), re.sub("^\\s|\\s*$", "", self.findChild(QLineEdit, "textsuporte").text()))
            tu=self.findChild(QTextEdit, "observations").toPlainText()
            if len(tu):
                self.signs_layer.changeAttributeValue(
                    self.sign.id(), self.sign.fieldNameIndex("observations"), self.findChild(QTextEdit, "observations").toPlainText())
            else:
                self.signs_layer.changeAttributeValue(
                    self.sign.id(), self.sign.fieldNameIndex("observations"),NULL)
            status = 1
            if is_not_a_sign:
                status = 3
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("status"), status)
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("saved"), True)
            self.signs_layer.changeAttributeValue(
                self.sign.id(), self.sign.fieldNameIndex("user"), os.getenv("USERNAME")
            )
            for k in ["1", "2", "suporte"]:
                if self.findChild(QCheckBox, f"remember{k}").isChecked():
                    words = set(self.read_autocomplete(f"text{k}"))
                    words.add(
                        re.sub("^\\s|\\s*$", "", self.findChild(QLineEdit, f"text{k}").text()))
                    self.write_autocomplete(f"text{k}", words)
            self.signs_layer.commitChanges()

            with open(os.path.join(os.path.dirname(__file__), f"filter.txt"), "a+") as fu:
                fu.write(f"{placa_style}\n")
            fu.close()
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
        self.findChild(QPushButton, "brasiltype").setIcon(QIcon(os.path.join(
            os.path.dirname(__file__), f"styles/symbols_br/{args[0]}.svg")))
        self.findChild(QTextEdit, "code_text").setText(args[0])
        self.code = args[0]

    def set_sign_face(self, *args, **kwargs):
        print("SETTTING SIGNS FACE")
        self.face = args[0][0:4]
        if self.code is None:
            return
        if not os.path.isfile(os.path.join(
                os.path.dirname(__file__), f"styles/symbols_br/{self.code}.svg")):
            return
        with open(os.path.join(
                os.path.dirname(__file__), f"styles/symbols_br/{self.code}.svg")) as fu:
            svg = fu.read()
        fu.close()

        if self.code == "R-15":
            svg = svg.replace(
                "</svg>", f'<text x="400" y="470" font-size="200" fill="black" text-anchor="middle" font-family="sans-serif">{self.face}</text></svg>')
        elif self.code == "R-19":
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
        self.sign_images_index += 1
        self.sign_images_index = self.sign_images_index % len(self.sign_images)
        self.navigate()

    def navigate(self):
        self.dl = SignDataDownloader(
            mapillary_key=self.key, image=self.sign_images[self.sign_images_index], fields='thumb_1024_url,computed_compass_angle,computed_geometry,captured_at,detections.value,detections.geometry')
        self.dl.taskCompleted.connect(self.show_image)
        QgsApplication.taskManager().addTask(self.dl)
        # self.geo_dl=SignDataDownloader(
        #    mapillary_key=self.key, image=self.sign_images[self.sign_images_index], fields='geometry', datatype="geometry")
        # self.geo_dl.taskCompleted.connect(self.show_geometry)
        # QgsApplication.taskManager().addTask(self.geo_dl)

    def backward(self):
        self.sign_images_index -= 1
        if self.sign_images_index < 0:
            self.sign_images_index = len(self.sign_images)-1
        self.navigate()

    def close(self):
        self.close_record()
        super().close()

    def connect_signals(self):
        self.findChild(
            QPushButton, "pushButton_cancel").clicked.connect(self.close)
        self.findChild(QPushButton, "pushButton_forward").clicked.connect(
            self.forward)
        self.findChild(QPushButton, "pushButton_back").clicked.connect(
            self.backward)

    def get_point_layer_by_name(self, name):
        layers = list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [
                      QgsWkbTypes.Point, QgsWkbTypes.MultiPoint] and x.name() == name, QgsProject.instance().mapLayers().values()))
        if layers:
            return layers[0]

    def show_image(self, *args, **kwargs):
        import base64
        import mapbox_vector_tile
        if self.dl.result is None:
            return
        cg = self.dl.result.get("computed_geometry")
        if cg is None:
            return
        geometries = list(filter(lambda x: x.get(
            "value") == self.sign["value"], self.dl.result.get("detections").get("data")))
        if len(geometries):
            canvas = self.get_canvas()
            canvas.reset_canvas()
            for geok in geometries:
                geo = geok.get('geometry')
                vector = base64.decodebytes(geo.encode('utf-8'))
                decoded_geometry = mapbox_vector_tile.decode(vector)
                detection_coordinates = decoded_geometry['mpy-or']['features'][0]['geometry']['coordinates']
                web = self.findChild(QWebView, "webView")
                pixel_coords = [[[x/4096 * web.width(), y/4096 * web.height()]
                                 for x, y in tuple(coord_pair)] for coord_pair in detection_coordinates]
                ih = int(pixel_coords[0][0][1]-pixel_coords[0][2][1])
                iw = int(pixel_coords[0][1][0]-pixel_coords[0][3][0])
                vy = [int(pixel_coords[0][3][0]), int(
                    web.height()-pixel_coords[0][2][1])-ih, iw, ih]
                canvas.draw_rectangle(vy, geok.get("value"))

        g = self.dl.result.get("computed_geometry").get("coordinates")
        self.streetview = f"http://maps.google.com/maps?q=&layer=c&cbll={g[1]},{g[0]}"
        self.mapillary = f"https://www.mapillary.com/app/?lat={g[1]}&lng={g[0]}&z=17&pKey={self.dl.result.get('id')}"
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
        # self.findChild(QWebView, "webView").load(
        #    QUrl(self.dl.result.get("thumb_1024_url")))
        self.findChild(QWebView, "webView").setHtml(f"<html>\
            <head></head>\
             <body style=\"background-size:100% 100%;background-image:url({self.dl.result.get('thumb_1024_url')})\"></body>\
             \
             \
             \
             \
                 </html>")
        # https://graph.mapillary.com/:image_id/detections

    def set_map_tool(self):
        canvas: QgsMapCanvas = self.findChild(QgsMapCanvas, "mapview")

        self.mapTool = RoadsSelector(canvas, self.roads_layer)
        self.mapTool.geomIdentified.connect(self.display_road)
        self.mapTool.setLayer(self.roads_layer)
        canvas: QgsMapCanvas = self.findChild(QgsMapCanvas, "mapview")
        canvas.setMapTool(self.mapTool)

    def display_road(self, *args, **kwargs):
        self.road_id = args[1][self.conf.get("roads_pk")]
        road_name = args[1][self.conf.get("roads_field_name")]
        self.findChild(QTextEdit, "road_segment").setText(road_name)
