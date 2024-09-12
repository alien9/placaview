from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QDialog, QWidget,QPushButton, QListView, QListWidget, QListWidgetItem, QCheckBox
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt.QtWidgets import QApplication, QWidget,  QLineEdit,  QFormLayout,  QHBoxLayout
from qgis.PyQt import uic, QtSvg
import os, re
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal
from qgis.gui import QgsFilterLineEdit

class SignsFilterItem(QWidget):
    check:QCheckBox
    changed = pyqtSignal(str, bool)
    
    def __init__(self, name, parent=None):
        super(SignsFilterItem, self).__init__(parent)
        self.row = QHBoxLayout()
        svgWidget = QtSvg.QSvgWidget(os.path.join(os.path.dirname(__file__), "styles", name))
        print(os.path.join(os.path.dirname(__file__),"styles",  name))
        svgWidget.setFixedWidth(30)
        svgWidget.setFixedHeight(30)
        self.row.addWidget(svgWidget)
        self.check=QCheckBox(text=name)
        self.check.name=name
        self.row.addWidget(self.check)
        self.setLayout(self.row)
        self.name=name
        self.check.stateChanged.connect(self.valueChanged)
        
    def setValue(self, value):
        self.check.setChecked(value)
        
    def valueChanged(self, *args):
        self.changed.emit(self.name, args[0]==2)

    def getValue(self):
        return self.check.isChecked()