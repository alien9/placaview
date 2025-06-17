from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget,QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox
from qgis.PyQt import QtSvg
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit,  QFormLayout,  QHBoxLayout
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit, QCompleter, QTextEdit,  QFormLayout,  QHBoxLayout, QGraphicsView, QVBoxLayout, QApplication, QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from qgis.PyQt import uic
#from qgis.gui import (QgsFieldComboBox, QgsMapLayerComboBox)
from qgis.core import QgsMapLayerProxyModel
from qgis.gui import QgsFilterLineEdit
from .composite_item import CompositeItem
from qgis.core import NULL

import os, re

FormClass, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'composite_selector.ui'))

class CompositeSelector(QDialog, FormClass):
    sign_names=None
    sign=None
    selected_signs=set()
    applyClicked = pyqtSignal(list, str)
    placas=[]

    def __init__(self, *args, **kwargs):
        super().__init__(parent=kwargs.get("parent"))
        self.setWindowTitle("Composite Sign")
        self.sign=kwargs.get("sign")
        self.layer=kwargs.get("layer")
        self.placas=kwargs.get("placas")
        self.roads=kwargs.get("roads")
        self.conf=kwargs.get("conf")
        self.setupUi(self)
        self.findChild(QPushButton, "pushButton_ok").clicked.connect(self.close)
        n=0

        vbox=QVBoxLayout()  
        for placa in self.placas:
            widget=self.findChild(QListWidget, "listWidget")
            item = QListWidgetItem(widget)
            icon=placa["value_code_face"]
            item.name="No name"
            if icon is None or icon==NULL or icon=="":
                icon=placa["value"]
            if placa["road"]==NULL:
                item.name="Unknown road"
            else:
                if self.conf.get("roads_field_name") in self.roads.getFeature(placa["road"]):
                    item.name=self.roads.getFeature(placa["road"])[self.conf.get("roads_field_name")]
            widget.addItem(item)
            row=CompositeItem(icon, str(item.name), placa.id(), self.sign["composite_id"])
            print(self.sign["composite_id"])
            row.setValue(self.sign["composite_id"] != NULL and (self.sign["composite_id"]==placa["composite_id"]))
            row.changed.connect(self.valueChanged)
            item.setSizeHint(row.minimumSizeHint())
            widget.setItemWidget(item, row)
            n+=1
            
    def valueChanged(self, *args, **kwargs):
        
        
        self.layer.startEditing()
        f=self.layer.getFeature(args[2])
        
        
        if args[1]:
            f.setAttribute(self.layer.fields().indexOf("composite_id"),args[3])
        else:
            f.setAttribute(self.layer.fields().indexOf("composite_id"),NULL)
        self.layer.updateFeature(f)
        self.layer.commitChanges()
        
        

