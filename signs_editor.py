from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal, QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget, QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit,  QFormLayout,  QHBoxLayout
from qgis.PyQt import uic
from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsTask)
from qgis.PyQt.QtWebKitWidgets import QWebView

from qgis.gui import QgsFilterLineEdit
import os
import requests
import re
from .signs_filter_item import SignsFilterItem

FormClass, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'signs_editor.ui'))


class SignDataDownloader(QgsTask):
    key = None
    image_id = None
    result = None

    def run(self):
        print("running")
        r = requests.get(
            f"https://graph.mapillary.com/{self.image_id}?access_token={self.key}&fields={self.fields}")
        if r.status_code == 200:
            self.result = r.json()
            print(self.result)
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

    def __init__(self, *args, **kwargs):
        super().__init__(parent=kwargs.get("parent"))
        self.setWindowTitle("Signs Editor")
        self.setupUi(self)
        self.connect_signals()
        print("signs editor")
        print(kwargs)
        self.key = kwargs.get('mapillary_key')
        self.sign_id = kwargs.get('sign')
        self.sign_images = kwargs.get("sign_images")

        if self.sign_images:
            self.sign_images_index = 0
            self.dl = SignDataDownloader(
                mapillary_key=self.key, image=self.sign_images[0], fields='thumb_1024_url')
            self.dl.taskCompleted.connect(self.show_image)
            QgsApplication.taskManager().addTask(self.dl)

    def connect_signals(self):
        self.findChild(
            QPushButton, "pushButton_cancel").clicked.connect(self.close)

    def show_image(self, *args, **kwargs):
        self.findChild(QWebView, "webView").load(
            QUrl(self.dl.result.get("thumb_1024_url")))
