import random, requests
from time import sleep

from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsTask)
from qgis.core import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtCore import *
from .tools import vt_bytes_to_geojson
from .equidistance_buffer import EquidistanceBuffer

MESSAGE_CATEGORY = 'Download task'

class RoadsMatcher(QgsTask):
    signs_layer:QgsVectorLayer
    roads_layer:QgsVectorLayer
    feature:QgsFeature
    conf:dict={}
    total:int
    feature_id:int
    
    def __init__(self, *args, **kwargs):
        super().__init__("Matching Roads")#, QgsTask.CanCancel) 
        self.conf=kwargs.get("conf")
        self.roads_layer=kwargs.get("roads_layer")
        self.signs_layer=self.get_signs_layer()
        self.roads_field_name=kwargs.get("roads_field_name")
        self.roads_pk=kwargs.get("roads_pk")
        self.total=kwargs.get("total")
        self.done=kwargs.get("done")
        self.feature_id=kwargs.get("feature_id")
        #self.on_finished=kwargs.get("on_finished")
       
        
        self.buffet = EquidistanceBuffer()
        QgsMessageLog.logMessage('Instanced task geocoder "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)
        return
    
    def get_signs_layer(self):
        layers = list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [QgsWkbTypes.Point, QgsWkbTypes.MultiPoint] and x.name(
        ) == "traffic signs", QgsProject.instance().mapLayers().values()))
        if layers:
            return layers[0]
        
    def run(self):
        print("RUN")
        QgsMessageLog.logMessage('Started task geocoder "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)
        index = QgsSpatialIndex(self.roads_layer.getFeatures(
        ), flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        n=0
        self.setProgress(100*self.done/self.total)
        
        print("top 1")
        feature:QgsFeature=self.signs_layer.getFeature(self.feature_id)
        n+=1
        print(f"will set ptogress to {100*self.done/self.total}")
        print("progresses")
        d = 50
        roads = []
        if self.isCanceled():
            return False
        geom = feature.geometry()
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
        print("GEOCOEDE COMNCLUDED")
        if len(roads) > 50 or d>300:
            #feature["out"]=1
            self.signs_layer.changeAttributeValue(feature.id(), feature.fieldNameIndex("out"),1)
        elif len(roads):
            print(f"has {len(roads)} roads")
            print(roads)
            f_roads=[]
            for r in roads:
                f=self.roads_layer.getFeature(r)
                distance=self.get_distance_from_road_to_sign(projected, f.geometry(), roads_xform)
                f_roads.append((distance,r))
            
            f_roads.sort()
            road_feature=self.roads_layer.getFeature(f_roads[0][1])
            print("road id")
            print(road_feature[self.roads_pk] is None)
            print(type(road_feature[self.roads_pk]))
            
            if type(road_feature[self.roads_pk]) is int:
                
                print("x",int(road_feature[self.roads_pk]))
                self.signs_layer.changeAttributeValue(feature.id(), feature.fieldNameIndex("road"),int(road_feature[self.roads_pk]))
                #feature["road"]=int(road_feature[self.roads_pk])
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

            if len(roads)>1:
                difference=f_roads[1][0]-f_roads[0][0]
                print("has difference")
                print(difference)
                self.signs_layer.changeAttributeValue(feature.id(), feature.fieldNameIndex("certain"),difference)
                #feature["certain"]=difference
                print("changeeeeeee")
                
        else:
            self.signs_layer.changeAttributeValue(feature.id(), feature.fieldNameIndex("out"),1)
            #feature["out"]=1
            print("oooooooooooooooooooooooooooooooooooooo")
        #signs_layer.updateFeature(feature)
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
        QgsMessageLog.logMessage(
            'Task "{name}" was cancelled'.format(name=self.description()),
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

