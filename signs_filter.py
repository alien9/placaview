from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget,QPushButton, QListView, QListWidget, QListWidgetItem
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit,  QFormLayout,  QHBoxLayout
from qgis.PyQt import uic
import os, re

FormClass, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'signs_filter.ui'))

class SignsFilter(QDialog, FormClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Signs Filter")
        self.setupUi(self)
        self.findChild(QPushButton, "pushButton_cancel").pressed.connect(self.close)
        for item in self.get_signs():
            self.findChild(QListView, "listVidget").addItem(item)
        
        
        
    def get_signs(self):
        return [re.split("(\.svg)$", filename).pop(0) for filename in os.listdir(os.path.join(os.path.dirname(__file__), 'styles/symbols'))]

        
    
