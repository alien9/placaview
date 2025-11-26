import random, requests
from time import sleep

from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsTask)
from qgis.core import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtWebEngineWidgets import QWebEngineView

from qgis.PyQt.QtCore import *
from .tools import vt_bytes_to_geojson
from .equidistance_buffer import EquidistanceBuffer

MESSAGE_CATEGORY = 'PlacaView'

class RoadsMatcher(QgsTask):
    signs_layer:QgsVectorLayer
    roads_layer:QgsVectorLayer
    feature:QgsFeature
    conf:dict={}
    total:int
    done:int=0
    feature_id:int
    
    def __init__(self, *args, **kwargs):
        super().__init__("Matching Roads", QgsTask.CanCancel) 
        self.conf=kwargs.get("conf")
        self.roads_layer=kwargs.get("roads_layer")
        self.signs_layer=self.get_signs_layer()
        self.roads_field_name=kwargs.get("roads_field_name")
        self.roads_pk=kwargs.get("roads_pk")
        self.total=kwargs.get("total")
        self.done=kwargs.get("done",0)
        self.feature_id=kwargs.get("feature_id")
        self.buffet = EquidistanceBuffer()
        QgsMessageLog.logMessage('Instanced task geocoder "{}" for {}'.format(
            self.description(), self.feature_id), MESSAGE_CATEGORY, Qgis.Info)
        return
    
    def get_signs_layer(self):
        layers = list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [QgsWkbTypes.Point, QgsWkbTypes.MultiPoint] and x.name(
        ) == "traffic signs", QgsProject.instance().mapLayers().values()))
        if layers:
            return layers[0]
        
    def run(self):
        QgsMessageLog.logMessage('Started task geocoder "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)
        index = QgsSpatialIndex(self.roads_layer.getFeatures(
        ), flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        n=0
        self.setProgress(0)
        request=QgsFeatureRequest(QgsExpression(" \"road\" is null and \"out\" is null"))
        #request.setLimit(100)
        if self.feature_id is not None:
            fids=[self.feature_id]
        else:
            fids=[f.id() for f in self.signs_layer.getFeatures(request)]
        total=len(fids)
        self.setProgress(0/total)
        top=0
        #self.signs_layer.startEditing()
        provider:QgsDataProvider=self.signs_layer.dataProvider()
        projector=None
        xform=None
        roads_xform=None
        while top<total:
            for fid in fids[top:top+10000]:
                feature=self.signs_layer.getFeature(fid)
                n+=1
                self.setProgress(100*n/total)
                d = 50
                roads = []
                if self.isCanceled():
                    return False
                geom = feature.geometry()
                if projector is None:
                    projector = QgsCoordinateReferenceSystem(
                        self.buffet.proj_string(geom))
                    xform = QgsCoordinateTransform(
                        self.signs_layer.crs(), projector, QgsProject.instance())
                    roads_xform = QgsCoordinateTransform(
                        self.roads_layer.crs(), projector, QgsProject.instance())
                gt = geom.asWkt()
                projected = QgsGeometry.fromWkt(gt)
                projected.transform(xform)
                while not len(roads) and d < 300:
                    boulder: QgsGeometry = self.buffet.buffer(
                        geom, d, self.signs_layer.crs()
                    )
                    roads = index.intersects(boulder.boundingBox())
                    if len(roads) and len(roads) < 100:
                        roads = list(filter(lambda x: boulder.intersects(
                            self.roads_layer.getFeature(x).geometry()), roads))
                    d += 30
                if len(roads) > 50 or d>300:
                    provider.enterUpdateMode()
                    provider.changeAttributeValues({feature.id():{self.signs_layer.fields().indexOf("out"):1}})
                    provider.leaveUpdateMode()
                    #self.signs_layer.changeAttributeValue(feature.id(), self.signs_layer.fields().indexOf("out"),1)
                if len(roads):
                    f_roads=[]
                    for r in roads:
                        road_feature=self.roads_layer.getFeature(r)
                        distance=self.get_distance_from_road_to_sign(projected, road_feature.geometry(), roads_xform)
                        f_roads.append((distance,r))
                    f_roads.sort()
                    road_feature=self.roads_layer.getFeature(f_roads[0][1])
                    #self.signs_layer.changeAttributeValue(feature.id(), self.signs_layer.fields().indexOf("road"),int(road_feature[self.roads_pk]))
                    provider.enterUpdateMode()
                    provider.changeAttributeValues({feature.id():{self.signs_layer.fields().indexOf("road"):int(road_feature[self.roads_pk])}})
                    provider.leaveUpdateMode()

                    if len(roads)>1:
                        #self.signs_layer.changeAttributeValue(feature.id(), self.signs_layer.fields().indexOf("certain"),f_roads[1][0]-f_roads[0][0])
                        provider.enterUpdateMode()
                        provider.changeAttributeValues({feature.id():{self.signs_layer.fields().indexOf("certain"):f_roads[1][0]-f_roads[0][0]}})
                        provider.leaveUpdateMode()
                    
                else:
                    provider.enterUpdateMode()
                    provider.changeAttributeValues({feature.id():{self.signs_layer.fields().indexOf("out"):1}})
                    provider.leaveUpdateMode()
                    #self.signs_layer.changeAttributeValue(feature.id(), self.signs_layer.fields().indexOf("out"),1)
            
            top+=10000
            #self.signs_layer.commitChanges(False)
        return True
    
    def geocode(self, feature):
        QgsMessageLog.logMessage('Started task geocoder "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)
        index = QgsSpatialIndex(self.roads_layer.getFeatures(
        ), flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        n=0
        self.setProgress(0)
        request=QgsFeatureRequest(QgsExpression(" \"road\" is null and \"out\" is null"))
        d = 50
        roads = []
        if self.isCanceled():
            return False
        geom = feature.geometry()
        if projector is None:
            projector = QgsCoordinateReferenceSystem(
                self.buffet.proj_string(geom))
            xform = QgsCoordinateTransform(
                self.signs_layer.crs(), projector, QgsProject.instance())
            roads_xform = QgsCoordinateTransform(
                self.roads_layer.crs(), projector, QgsProject.instance())
        gt = geom.asWkt()
        projected = QgsGeometry.fromWkt(gt)
        projected.transform(xform)
        provider:QgsDataProvider=self.signs_layer.dataProvider()
        while not len(roads) and d < 300:
            boulder: QgsGeometry = self.buffet.buffer(
                geom, d, self.signs_layer.crs()
            )
            roads = index.intersects(boulder.boundingBox())
            if len(roads) and len(roads) < 100:
                roads = list(filter(lambda x: boulder.intersects(
                    self.roads_layer.getFeature(x).geometry()), roads))
            d += 30
        if len(roads) > 50 or d>300:
            provider.enterUpdateMode()
            provider.changeAttributeValues({feature.id():{self.signs_layer.fields().indexOf("out"):1}})
            provider.leaveUpdateMode()
            #self.signs_layer.changeAttributeValue(feature.id(), self.signs_layer.fields().indexOf("out"),1)
        if len(roads):
            f_roads=[]
            for r in roads:
                road_feature=self.roads_layer.getFeature(r)
                distance=self.get_distance_from_road_to_sign(projected, road_feature.geometry(), roads_xform)
                f_roads.append((distance,r))
            f_roads.sort()
            road_feature=self.roads_layer.getFeature(f_roads[0][1])
            provider.enterUpdateMode()
            provider.changeAttributeValues({feature.id():{self.signs_layer.fields().indexOf("road"):int(road_feature[self.roads_pk])}})
            provider.leaveUpdateMode()

            if len(roads)>1:
                provider.enterUpdateMode()
                provider.changeAttributeValues({feature.id():{self.signs_layer.fields().indexOf("certain"):f_roads[1][0]-f_roads[0][0]}})
                provider.leaveUpdateMode()
            
        else:
            provider.enterUpdateMode()
            provider.changeAttributeValues({feature.id():{self.signs_layer.fields().indexOf("out"):1}})
            provider.leaveUpdateMode()
        return True

    
    def get_distance_from_road_to_sign(self, sign_geometry, road_geometry, xform):
        r = QgsGeometry(road_geometry)
        s = QgsGeometry(sign_geometry)
        r.transform(xform)
        return r.distance(s)
        
    def finished(self, result):        
        QgsMessageLog.logMessage(
            'Task "{name}" was finished'.format(name=self.description()),
            MESSAGE_CATEGORY, Qgis.Info)
        #self.on_finished()
                
    def cancel(self):
        try:
            QgsMessageLog.logMessage(
                'Task "{name}" was cancelled'.format(name=self.description()),
                MESSAGE_CATEGORY, Qgis.Info)
            super().cancel()
        except:
            pass
        

