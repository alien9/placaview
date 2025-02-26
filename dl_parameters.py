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
from qgis.PyQt.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGridLayout, QDialog
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
from qgis.gui import QgsMapToolIdentifyFeature, QgsDateEdit, QgsMessageBar


ParametersFormClass, eck = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dl_parameters.ui'))



class DownloadParameters(QDialog, ParametersFormClass):
    applyClicked = pyqtSignal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__(parent=kwargs.get("parent"))
        self.setupUi(self)
        self.findChild(
            QPushButton, "pushButton_cancel").clicked.connect(self.close)
        self.findChild(
            QPushButton, "pushButton_download").clicked.connect(self.download)
    
    def download(self, *args, **kwargs):
        params={}
        fro=self.findChild(QgsDateEdit, "last_from").date()
        if fro is not None:
            if fro.year()>0:
                QgsMessageLog.logMessage('last from "{}"'.format(
                str(fro)), "Messages", Qgis.Info)
                params["start_last_seen_at"]=datetime.datetime(fro.year(), fro.month(), fro.day()).isoformat()
        fro=self.findChild(QgsDateEdit, "last_to").date()
        if fro is not None:
            if fro.year()>0:
                params["end_last_seen_at"]=datetime.datetime(fro.year(), fro.month(), fro.day()).isoformat()
        fro=self.findChild(QgsDateEdit, "first_from").date()
        if fro is not None:
            if fro.year()>0:
                params["start_first_seen_at"]=datetime.datetime(fro.year(), fro.month(), fro.day()).isoformat()
        fro=self.findChild(QgsDateEdit, "first_to").date()
        if fro is not None:
            if fro.year()>0:
                params["end_first_seen_at"]=datetime.datetime(fro.year(), fro.month(), fro.day()).isoformat()
        fro=self.findChild(QLineEdit, "term").text()
        if fro is not None:
            params["object_values"]=fro
        
        self.applyClicked.emit(params)
        self.close()