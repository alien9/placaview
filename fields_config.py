from venv import logger
from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSize, QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget,QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit,  QFormLayout,  QHBoxLayout
from qgis.PyQt import uic
from qgis.core import QgsMapLayerProxyModel
from qgis.gui import QgsFilterLineEdit
import os, re, pathlib
from .fields_config_item import FieldsConfigItem

FormClass, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'fields_config.ui'))

from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class FieldsConfig(QDialog, FormClass):
    """Minimal dialog similar to SignsFilter that displays an empty element."""
    applyClicked = pyqtSignal(list)
    fields=[]
    def __init__(self, parent=None, fields=[]):
        super().__init__(parent)
        self.setWindowTitle("Fields Configuration")
        self.setModal(True)
        self.setupUi(self)
        self.load_conf()
        # load CSV configuration if present
        self.fields=fields
        self.render_fields(self.load())
        self.findChild(QPushButton, "pushButton_cancel").clicked.connect(self.close)
        self.findChild(QPushButton,"pushButton_ok").clicked.connect(self.save)

    def render_fields(self, fields_config):
        """Render fields in the QListWidget from self.fields_config."""
        widget = self.findChild(QListWidget, "listWidget")
        if widget is None:
            return
        widget.clear()
        if fields_config is not None:
            for field in fields_config:
                item = QListWidgetItem(widget)
                fci = FieldsConfigItem(field)
                fci.changed.connect(self.on_field_changed)
                item.setSizeHint(QSize(widget.width(), 30))
                widget.setItemWidget(item, fci)
    
    def on_field_changed(self, name: str, enabled: bool):
        """Handle changes from FieldsConfigItem instances."""
        # Placeholder for handling changes if needed
        values=self.get_fields_values()
        if len(values):
            values=list(filter(lambda v: v['name']!='' and v['name'] is not None, values))
            values.append({'name': '', 'type': 'Text', 'enabled': False})
            self.render_fields(values)
        
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # empty element (label intentionally left blank)
        self.empty_label = QLabel("", self)
        self.empty_label.setObjectName("empty_label")
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)

        # simple close button
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        

    def setText(self, text: str):
        """Optional helper
        self.empty_label.setText(text) to set label text."""
        self.empty_label.setText(text)
        
    def load_conf(self):
        patty=f'{QgsProject.instance().fileName()}_data/'
        con=pathlib.Path(f"{patty}fields.ini")
        if not con.is_file():
            con.touch()
        self.fields=open(con).readlines()

    def get_fields_values(self):
        list_widget = self.findChild(QListWidget, "listWidget")
        if list_widget is None:
            return

        objects = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            widget = list_widget.itemWidget(item)
            if widget is None:
                continue
            # extract values from FieldsConfigItem
            name = ""
            ftype = "Text"
            enabled = False
            try:
                name = widget.name_text.text().strip()
            except Exception:
                name = str(widget)
            try:
                ftype = widget.getType() if hasattr(widget, 'getType') else 'Text'
            except Exception:
                ftype = 'Text'
            try:
                enabled = widget.getValue() if hasattr(widget, 'getValue') else False
            except Exception:
                enabled = False
            if name is not None:
                if name!="":
                    objects.append({'name': name, 'type': ftype, 'enabled': enabled})
        return objects
        
    def save(self):
        """Save the fields configuration to a CSV file in the project's _data folder.
        CSV columns: name,type,enabled
        """
        patty = f'{QgsProject.instance().fileName()}_data/'
        from pathlib import Path
        p = Path(patty)
        p.mkdir(parents=True, exist_ok=True)
        out = p / 'fields.csv'

        list_widget = self.findChild(QListWidget, "listWidget")
        if list_widget is None:
            return

        lines = ["name,type,enabled"]
        objects = self.get_fields_values()
        for i in range(len(objects)):
            lines.append(f'{objects[i]["name"]},{objects[i]["type"]},{1 if objects[i]["enabled"] else 0}')
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write("\n".join(lines))

        # keep previous signal behavior for compatibility
        try:
            self.applyClicked.emit(objects)
        except Exception as xx:
            logger.warning("Failed to emit applyClicked signal from FieldsConfig.")
            logger.warning(str(xx))
        self.close()
    
    def load(self):
        """Load fields configuration from project's _data/fields.csv into self.fields_config.
        Expected CSV columns: name,type,enabled
        """
        from pathlib import Path
        import csv

        patty = f'{QgsProject.instance().fileName()}_data/'
        p = Path(patty)
        p.mkdir(parents=True, exist_ok=True)
        out = p / 'fields.csv'

        fields_config = []
        
        # ensure fields.csv exists with header if absent so load can proceed
        if not out.is_file():
            try:
                with open(out, 'w', encoding='utf-8') as fh:
                    fh.write('name,type,enabled\n')
            except Exception:
                # if we can't create the file, return empty list to avoid breaking callers
                return []

        try:
            with open(out, newline='', encoding='utf-8') as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    # normalize keys
                    name = row.get('name', '').strip()
                    ftype = row.get('type', 'Text').strip()
                    enabled = row.get('enabled', '0').strip()
                    try:
                        enabled_bool = bool(int(enabled))
                    except Exception:
                        enabled_bool = enabled.lower() in ('1', 'true', 'yes')
                    if name!='':
                        fields_config.append({'name': name, 'type': ftype, 'enabled': enabled_bool})
            fields_config.append({'name': '', 'type': 'Text', 'enabled': False})
        except Exception:
            # on error keep fields_config empty
            fields_config = []
        return fields_config
        
    
    def add_empty_item(self):
        """Add an item to the QListWidget with type 'Text' and name 'null'."""
        widget = self.findChild(QListWidget, "listWidget")
        if widget is None:
            return
        field = {'name': '', 'type': 'Text', 'enabled': False}
        item = QListWidgetItem(widget)
        fci = FieldsConfigItem(field)
        item.setSizeHint(QSize(widget.width(), 30))
        widget.setItemWidget(item, fci)

        widget.addItem(item)
        
    def clear_invalid_items(self):
        """Clear all items from the QListWidget."""
        widget = self.findChild(QListWidget, "listWidget")
        if widget is None:
            return
        
        widget.clear()