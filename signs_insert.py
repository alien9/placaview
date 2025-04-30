from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt import uic
from qgis.core import QgsStyle, QgsSymbol,QgsRendererCategory, QgsSvgMarkerSymbolLayer
from qgis.gui import QgsMapToolEmitPoint, QgsMapToolIdentify

class SignsInsert(QgsMapToolEmitPoint):

    signInserted = pyqtSignal(object, object)

    #def __init__(self, canvas):
        #QgsMapToolEmitPoint.__init__(self, canvas)
        #canvas.setMapTool(self)
    """ 
    def insert_sign_at(self, *args, **kwargs):
        print("inserting sifng oooo")
        print(args)
                    
    def canvasReleaseEvent(self, mouseEvent):
        print("canvas release")
            
    def canvasPressEvent(self, event):
        print("presss")
    """
        
