from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget,QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit,  QFormLayout,  QHBoxLayout
from qgis.PyQt import uic
from qgis.gui import (QgsFieldComboBox, QgsMapLayerComboBox)
from qgis.core import QgsMapLayerProxyModel
from qgis.gui import QgsFilterLineEdit
import os, re
from .signs_filter_item import SignsFilterItem

FormClass, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'signs_filter.ui'))

class SignsFilter(QDialog, FormClass):
    sign_names=None
    selected_signs=set()
    applyClicked = pyqtSignal(list, str)
        
    def __init__(self, *args, **kwargs):
        super().__init__(parent=kwargs.get("parent"))
        self.selected_signs=set(kwargs.get("filter", []))
        print("isso eh selected signs")
        self.sign_names=sorted(kwargs.get("values",[]))
        self.setWindowTitle("Signs Filter")
        self.setupUi(self)
        self.search_term=QgsFilterLineEdit()
        layout=self.findChild(QHBoxLayout, "searchLayout")
        layout.addWidget(self.search_term)
        for name in self.sign_names: #get_signs():
            widget=self.findChild(QListWidget, "listWidget")
            item = QListWidgetItem(widget)
            item.name=name
            widget.addItem(item)
            row=SignsFilterItem(name)
            row.setValue(name in self.selected_signs)
            row.changed.connect(self.signs_filter_item_changed)
            item.setSizeHint(row.minimumSizeHint())
            widget.setItemWidget(item, row)
        self.connect_signals()
        combover:QgsMapLayerComboBox=self.findChild(QgsMapLayerComboBox, "mMapLayerComboBox")
        combover.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        combover.setAllowEmptyLayer(True)
        combover.setLayer(None)
        if kwargs["layer_filter"]:
            combover.setLayer(kwargs["layer_filter"])
            
            
    def get_signs(self):
        if not self.sign_names:
            filename=os.path.join(os.path.dirname(__file__), "existing.txt")
            if os.path.isfile(filename):
                with open(filename, "r") as fu:
                    self.sign_names=[n[:-1] for n in fu.readlines()]
                fu.close()
            else:    
                self.sign_names= sorted([re.split("(\.svg)$", filename).pop(0) for filename in os.listdir(os.path.join(os.path.dirname(__file__), 'styles/symbols'))])
        return self.sign_names
    
    @pyqtSlot(str, bool)
    def signs_filter_item_changed(self, *args):
        if not args[1]:
            self.selected_signs.remove(args[0])
        else:
            self.selected_signs.add(args[0])
            self.sign_names.sort()

    @pyqtSlot()
    def save_filter(self):
        widget=self.findChild(QListWidget, "listWidget")
        l=self.findChild(QgsMapLayerComboBox, "mMapLayerComboBox").currentLayer()
        layer_filter=None
        if l:
            layer_filter=l.name()            
        self.applyClicked.emit(list(self.selected_signs),layer_filter)
        self.close()
                    
    def load_filter(self):
        return []
    
    @pyqtSlot()
    def filter_list(self, *args, **kwargs):
        print("filtering list")
        term=self.search_term.value()
        #filtered_list = set(filter(lambda x: term in x, self.get_signs()))
        widget=self.findChild(QListWidget, "listWidget")
        for i in range(widget.count()):
            widget.item(i).setHidden(term not in widget.item(i).name)
        c=self.findChild(QCheckBox, "select_all")
        c.blockSignals(True)
        c.setChecked(False)
        c.blockSignals(False)
            
    @pyqtSlot()
    def toggle_selection(self):
        widget=self.findChild(QListWidget, "listWidget")
        for i in range(widget.count()):
            if not widget.item(i).isHidden():
                w=widget.itemWidget(widget.item(i))
                w.setValue(not w.getValue())
    
    def select_deselect_all(self, *args):
        widget=self.findChild(QListWidget, "listWidget")
        for i in range(widget.count()):
            if not widget.item(i).isHidden():
                widget.itemWidget(widget.item(i)).setValue(args[0]==2)
                
    
            
    def connect_signals(self):
        self.findChild(QPushButton, "pushButton_ok").clicked.connect(self.save_filter)
        self.findChild(QPushButton, "pushButton_cancel").clicked.connect(self.close)
        self.findChild(QPushButton, "pushButton_toggle_selection").clicked.connect(self.toggle_selection)
        self.findChild(QCheckBox, "select_all").stateChanged.connect(self.select_deselect_all)
        self.search_term.valueChanged.connect(self.filter_list)
    
    