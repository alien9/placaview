from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt import uic
from qgis.core import QgsStyle, QgsSymbol,QgsRendererCategory, QgsSvgMarkerSymbolLayer
from qgis.gui import QgsMapToolIdentifyFeature, QgsMapToolIdentify

class RoadsSelector(QgsMapToolIdentifyFeature):

    geomIdentified = pyqtSignal(object, object)

    def __init__(self, canvas, layer):
        self.canvas = canvas
        self.layer = layer #self.iface.activeLayer()
        QgsMapToolIdentifyFeature.__init__(self, self.canvas, self.layer)
        self.featureIdentified.connect(self.identify)
        self.canvas.setMapTool(self)
        
    def active_changed(self, layer):
        try:
            self.layer.removeSelection()
        except:
            #the layer doesnt exist anymore
            pass
        #if isinstance(layer, QgsVectorLayer) and layer.isSpatial():
        #    self.layer = layer
        #    self.setLayer(self.layer)
            
    def canvasReleaseEvent(self, mouseEvent):
        results = self.identify(mouseEvent.x(), mouseEvent.y(), self.TopDownStopAtFirst, [self.layer], self.VectorLayer)       
        if results:
            self.geomIdentified.emit(results[0].mLayer, results[0].mFeature)
            
    def canvasPressEvent(self, event):
        self.layer.removeSelection()
        found_features = self.identify(event.x(), event.y(), [self.layer], QgsMapToolIdentify.TopDownAll)
        if found_features:
            self.layer.selectByIds([f.mFeature.id() for f in found_features], QgsVectorLayer.AddToSelection)
        
    def deactivate(self):
        self.layer.removeSelection()
        
        
