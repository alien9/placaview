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
import threading
import time

FormClass, eck = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'browser.ui'))

class Browser(QtWidgets.QDockWidget, FormClass):
    url="about:blank"
    def __init__(self, parent=None):
        """Constructor."""
        super(Browser, self).__init__(parent)
        self.setupUi(self)
        thread1 = threading.Thread(target=self.task, args=("One",))
        thread1.start()
        #thread1.join()

    def task(self, name):
        print(f"Thread {name}: starting")
        while True:
            time.sleep(200)
            print(self.url)
            print(self.findChild(QWebEngineView, "webView").url())

    def open_mapillary(self):
        QDesktopServices.openUrl(QUrl(self.mapillary))

    def open_streetview(self):
        QDesktopServices.openUrl(QUrl(self.streetview))

    def spinners(self):
        self.findChild(QWebEngineView, "webView").load(
            QUrl(f"file://{os.path.dirname(__file__)}/styles/lg.gif"))

    def close(self):
        super().close()
