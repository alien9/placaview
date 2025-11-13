from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget,QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox, QComboBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit,  QFormLayout,  QHBoxLayout
from qgis.PyQt import uic, QtSvg
import os, re
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal
from qgis.gui import QgsFilterLineEdit

class FieldsConfigItem(QWidget):
    check:QCheckBox
    changed = pyqtSignal(str, bool)
    
    def __init__(self, field, parent=None):
        super(FieldsConfigItem, self).__init__(parent)
        # store provided field name
        self.name = field

        # layout
        self.row = QHBoxLayout()
        self.row.setContentsMargins(5,5,5,5)

        # editable name
        self.name_text = QLineEdit(text=field['name'] if 'name' in field else "")
        self.name_text.setFixedHeight(25)

        # type combo: Text (default) or Numeric
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Text", "Numeric"])
        self.type_combo.setCurrentText(field['type'] if 'type' in field else "Text")
        self.type_combo.setFixedHeight(25)

        # checkbox
        self.check = QCheckBox()
        self.check.setChecked(field['enabled'] if 'enabled' in field else False)
        # assemble widgets
        self.row.addWidget(self.name_text)
        self.row.addWidget(self.type_combo)
        self.row.addWidget(self.check)
        self.setLayout(self.row)

        # signals
        self.check.stateChanged.connect(self.valueChanged)
        self.name_text.textChanged.connect(self._name_changed)
        self.type_combo.currentTextChanged.connect(self._type_changed)
        
    def _name_changed(self, text):
        self.name = text

    def _type_changed(self, text):
        # placeholder if external listeners are needed in future
        pass
        
    def setValue(self, value):
        self.check.setChecked(value)
        
    def valueChanged(self, *args):
        self.changed.emit(self.name['name'], args[0]==2)

    def getValue(self):
        return self.check.isChecked()

    def getType(self):
        """Return currently selected type ('Text' or 'Numeric')."""
        return str(self.type_combo.currentText())

    def setType(self, value):
        """Set the combo value ('Text' or 'Numeric')."""
        if value in ("Text", "Numeric"):
            self.type_combo.setCurrentText(value)