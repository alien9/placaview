from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsProcessingFeatureBasedAlgorithm, 
    QgsProcessingParameterDistance, QgsPoint, QgsFeature, QgsGeometry, 
    QgsWkbTypes, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject)
    

class EquidistanceBuffer(QgsProcessingFeatureBasedAlgorithm ):
    """
    This algorithm takes a vectorlayer and creates equidistance bufers.
    """
    DISTANCE = 'DISTANCE'
    SEGMENTS = 5   
    END_CAP_STYLE = QgsGeometry.CapRound 
    JOIN_STYLE = QgsGeometry.JoinStyleRound
    MITER_LIMIT = 2.0
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return EquidistanceBuffer()

    def name(self):
        return 'equidistance_buffer'

    def displayName(self):
        return self.tr('Equidistance Buffer')

    def group(self):
        return self.tr('scripts')

    def groupId(self):
        return 'scripts'

    def outputName(self):
        return self.tr('buffers')
        
    def shortHelpString(self):
        return self.tr(
            'This algorithm creates equidistant buffers for vector layers. \
            Each geometry is transformed to a Azimuthal Equidistant projection \
            centered at that geometry, buffered and transformed back to the \
            original projection.')

    def __init__(self):
        super().__init__()
    
    def inputLayerTypes(self):
        return [QgsProcessing.TypeVector]
        
    def outputWkbType(self, input_wkb_type):
        return QgsWkbTypes.Polygon
        
    def initParameters(self, config=None):
        self.addParameter(
            QgsProcessingParameterDistance(
                self.DISTANCE,
                'Buffer Distance (meters)',
                defaultValue=10000
                ))
                
    def prepareAlgorithm(self, parameters, context, feedback):
        self.distance = self.parameterAsDouble(
            parameters,
            self.DISTANCE,
            context)
        source = self.parameterAsSource(parameters, 'INPUT', context)
        self.source_crs = source.sourceCrs()
        if not self.source_crs.isGeographic():
            feedback.reportError('Layer CRS must be a Geograhpic CRS for this algorithm')
            return False
        return super().prepareAlgorithm(parameters, context, feedback)

    def processFeature(self, feature, context, feedback):
        geometry = feature.geometry()
        # For point features, centroid() returns the point itself
        centroid = geometry.centroid()
        x = centroid.asPoint().x()
        y = centroid.asPoint().y()
        proj_string = 'PROJ4:+proj=aeqd +ellps=WGS84 +lat_0={} +lon_0={} +x_0=0 +y_0=0'.format(y, x)
        dest_crs = QgsCoordinateReferenceSystem(proj_string)
        xform = QgsCoordinateTransform(self.source_crs, dest_crs, QgsProject.instance())
        geometry.transform(xform)
        buffer = geometry.buffer(self.distance, self.SEGMENTS, self.END_CAP_STYLE, self.JOIN_STYLE, self.MITER_LIMIT)
        buffer.transform(xform, QgsCoordinateTransform.ReverseTransform)
        feature.setGeometry(buffer)
        return [feature]
    
    def buffer(self, geometry:QgsGeometry, distance, source_crs:QgsCoordinateReferenceSystem):
        centroid = geometry.centroid()
        x = round(centroid.asPoint().x(), 2)
        y = round(centroid.asPoint().y(), 2)
        proj_string = 'PROJ4:+proj=aeqd +ellps=WGS84 +lat_0={} +lon_0={} +x_0=0 +y_0=0'.format(y, x)
        dest_crs = QgsCoordinateReferenceSystem(proj_string)
        xform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
        b=geometry.asWkt()
        g=QgsGeometry.fromWkt(b)
        g.transform(xform)
        buffer = g.buffer(distance, self.SEGMENTS, self.END_CAP_STYLE, self.JOIN_STYLE, self.MITER_LIMIT)
        buffer.transform(xform, QgsCoordinateTransform.ReverseTransform)
        return buffer
    
    def proj_string(self, geometry:QgsGeometry):
        centroid = geometry.centroid()
        x = round(centroid.asPoint().x(), 2)
        y = round(centroid.asPoint().y(), 2)
        return 'PROJ4:+proj=aeqd +ellps=WGS84 +lat_0={} +lon_0={} +x_0=0 +y_0=0'.format(y, x)
