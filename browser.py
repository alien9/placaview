from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject, QgsApplication
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal, QUrl, QSize
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDesktopWidget, QWidget, QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox, QComboBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit, QCompleter, QTextEdit,  QFormLayout,  QHBoxLayout, QGraphicsView, QVBoxLayout, QApplication, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
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
from qgis.PyQt.QtWebEngineWidgets import QWebEngineView
from qgis.gui import QgsMapCanvas, QgsMapToolIdentifyFeature
from qgis.PyQt import QtGui, QtWidgets, uic
from .equidistance_buffer import EquidistanceBuffer
from .detection_canvas import DetectionCanvas
from qgis.gui import QgsFilterLineEdit
from qgis.core import NULL
import os
import requests
import re
import json
import shutil
import datetime
from .roads_selector import RoadsSelector
import base64
import mapbox_vector_tile
FormClass, eck = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'browser.ui'))

class Browser(QtWidgets.QDockWidget, FormClass):
    url="about:blank"
    canvas: DetectionCanvas=None
    
    def __init__(self, parent=None):
        """Constructor."""
        super(Browser, self).__init__(parent)
        self.setupUi(self)

    def open_mapillary(self):
        QDesktopServices.openUrl(QUrl(self.mapillary))

    def open_streetview(self):
        QDesktopServices.openUrl(QUrl(self.streetview))

    def spinners(self):
        self.findChild(QWebEngineView, "webView").load(
            QUrl(f"file://{os.path.dirname(__file__)}/styles/lg.gif"))

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


    def close(self):
        super().close()

    def get_canvas(self):
        if self.canvas is None:
            self.canvas = DetectionCanvas()
            grid: QGridLayout = self.findChild(QGridLayout, "gridLayout")
            grid.addWidget(self.canvas, 0, 0, Qt.AlignCenter)
            self.canvas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on=True)
            self.canvas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        return self.canvas
    
    def draw_geometries(self, geometries):
        canvas = self.get_canvas()
        canvas.reset_canvas()
        for geok in geometries:
            geo = geok.get('geometry')
            vector = base64.decodebytes(geo.encode('utf-8'))
            decoded_geometry = mapbox_vector_tile.decode(vector)
            detection_coordinates = decoded_geometry['mpy-or']['features'][0]['geometry']['coordinates']
            web = self.findChild(QWebEngineView, "webView")
            pixel_coords = [[[x/4096 * web.width(), y/4096 * web.height()]
                                for x, y in tuple(coord_pair)] for coord_pair in detection_coordinates]
            ih = int(pixel_coords[0][0][1]-pixel_coords[0][2][1])
            iw = int(pixel_coords[0][1][0]-pixel_coords[0][3][0])
            vy = [int(pixel_coords[0][3][0]), int(
                web.height()-pixel_coords[0][2][1])-ih, iw, ih]
            canvas.draw_rectangle(vy, geok.get("value"))
