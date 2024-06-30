from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal, QUrl, QSize
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget, QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QGridLayout, QApplication, QWidget,  QLineEdit,  QFormLayout,  QHBoxLayout, QGraphicsView, QVBoxLayout, QApplication, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from qgis.PyQt import uic
from qgis.PyQt.QtSvg import QGraphicsSvgItem, QSvgRenderer, QSvgWidget
import qgis.PyQt.QtSvg
from qgis.PyQt.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from qgis.PyQt.QtSvg import QSvgWidget, QSvgRenderer
from qgis.PyQt.QtGui import QTransform
from functools import partial


from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsTask)
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.gui import QgsMapCanvas
from .equidistance_buffer import EquidistanceBuffer
from qgis.gui import QgsFilterLineEdit
import os
import requests
import re
from .signs_filter_item import SignsFilterItem

FormClass, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'placa_selector.ui'))


class PlacaSelector(QDialog, FormClass):
    key = None
    sign_id = None
    sign_images: list = []
    sign_images_index = -1
    applyClicked = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(parent=kwargs.get("parent"))

        self.setWindowTitle("Select the Sign")
        self.setupUi(self)
        layout: QGridLayout = self.findChild(QGridLayout, "gridLayout")
        filename = os.path.join(os.path.dirname(__file__), "existing.txt")
        """ self.placas = [fu.replace(".svg", "") for fu in os.listdir(
            os.path.join(os.path.dirname(__file__), "styles/symbols_br"))] """
        self.placas=kwargs.get("placas", None)
        if not self.placas:
            self.placas=[fu[:-1] for fu in open(os.path.join(os.path.dirname(__file__), "styles/codes_br.txt"))]
        r=0
        c=0
        for p in self.placas:
            button = QPushButton("", self)
            button.setAccessibleName(p)
            button.setFixedSize(QSize(50,50))
            button.setIcon(QIcon(os.path.join(os.path.dirname(__file__),f"styles/symbols_br/{p}.svg")))
            button.setIconSize(QSize(40,40))
            button.setToolTip(p)    
            button.clicked.connect(partial(self.apply, p))
            layout.addWidget(button, r, c)
            c+=1
            if c>18:
                r+=1
                c=0 
            #button.setGeometry(200, 150, 100, 40)

    def apply(self, name):
        self.applyClicked.emit(name)
        self.close()