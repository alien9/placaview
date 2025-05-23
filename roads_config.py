from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget,QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit,  QFormLayout,  QHBoxLayout, QComboBox
from qgis.PyQt import uic

from qgis.gui import QgsFilterLineEdit
import os, re

FormClass, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'roads_config.ui'))

class RoadsConfig(QDialog, FormClass):
    applyClicked = pyqtSignal(str, str, str)
    field:str = None
    roads_pk:str=None
    
    def __init__(self, *args, **kwargs):
        super().__init__(parent=kwargs.get("parent"))
        self.app=kwargs.get("app")
        self.field=kwargs.get("field")
        self.roads_pk=kwargs.get("roads_pk")
        self.setWindowTitle("Select Roads Layer")
        self.setupUi(self)
        self.connect_signals()
        self.findChild(QComboBox, "roadsLayerComboBox").addItems(kwargs.get("roads"))
        if kwargs.get("road"):
            if kwargs.get("road") in kwargs.get("roads"):
                self.findChild(QComboBox, "roadsLayerComboBox").setCurrentIndex(kwargs.get("roads").index(kwargs.get("road")))
            
    @pyqtSlot()
    def set_roads_layer(self):
        widget=self.findChild(QListWidget, "listWidget")
        self.applyClicked.emit(self.findChild(QComboBox, "roadsLayerComboBox").currentText(), self.findChild(QComboBox, "fieldNameComboBox").currentText(), self.findChild(QComboBox, "fieldPkComboBox").currentText())
        self.close()
                    
    def load_fields(self, *args, **kwargs):
        layer=self.app.get_line_by_name(self.findChild(QComboBox, "roadsLayerComboBox").currentText())
        co=self.findChild(QComboBox, "fieldNameComboBox")
        co.clear()
        f=[field.name() for field in layer.fields()]
        co.addItems(f)
        if self.field:
            if self.field in f:
                co.setCurrentIndex(f.index(self.field))
        co=self.findChild(QComboBox, "fieldPkComboBox")
        co.clear()
        f=[field.name() for field in layer.fields()]
        co.addItems(f)
        if self.roads_pk:
            if self.roads_pk in f:
                co.setCurrentIndex(f.index(self.roads_pk))
            
    def connect_signals(self):
        self.findChild(QPushButton, "pushButton_ok").clicked.connect(self.set_roads_layer)
        self.findChild(QPushButton, "pushButton_cancel").clicked.connect(self.close)
        self.findChild(QComboBox, "roadsLayerComboBox").currentTextChanged.connect(self.load_fields)


    
    