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
    
    def __init__(self, *args, **kwargs):
        print(kwargs)
        super().__init__("Matching Roads", QgsTask.CanCancel)
        self.roads_layer=kwargs.get("roads_layer")
        self.signs_layer=kwargs.get("signs_layer")
        self.roads_field_name=kwargs.get("roads_field_name")
        self.roads_pk=kwargs.get("roads_pk")
        self.on_finished=kwargs.get("on_finished")
       
        
        self.buffet = EquidistanceBuffer()
        QgsMessageLog.logMessage('Instanced task geocoder "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)
        return

    def run(self):
        QgsMessageLog.logMessage('Started task geocoder "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)
        index = QgsSpatialIndex(self.roads_layer.getFeatures(
        ), flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        total=self.signs_layer.featureCount()
        print(f"have {total} to do!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        n=0
        print("n", n)
        
        print("create req")
        request=QgsFeatureRequest(QgsExpression(" \"road\" is null and \"out\" is null"))
        fids=[f.id() for f in self.signs_layer.getFeatures(request)]
        total=len(fids)
        top=0
        while top<total:
            self.signs_layer.startEditing()
            for fid in fids[top:top+10000]:
                feature=self.signs_layer.getFeature(fid)
                print(f"done {n} {top}")
                n+=1
                self.setProgress(100*n/total)
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
                if len(roads) > 50 or d>300:
                    self.signs_layer.changeAttributeValue(feature.id(), self.signs_layer.fields().indexOf("out"),1)
                if len(roads):
                    f_roads=[]
                    for r in roads:
                        road_feature=self.roads_layer.getFeature(r)
                        distance=self.get_distance_from_road_to_sign(projected, road_feature.geometry(), roads_xform)
                        f_roads.append((distance,r))
                    f_roads.sort()
                    road_feature=self.roads_layer.getFeature(f_roads[0][1])
                    self.signs_layer.changeAttributeValue(feature.id(), self.signs_layer.fields().indexOf("road"),int(road_feature[self.roads_pk]))
                    if len(roads)>1:
                        self.signs_layer.changeAttributeValue(feature.id(), self.signs_layer.fields().indexOf("certain"),f_roads[1][0]-f_roads[0][0])
                        
                else:
                    self.signs_layer.changeAttributeValue(feature.id(), self.signs_layer.fields().indexOf("out"),1)
                self.signs_layer.commitChanges()
            print("done", n)
            top+=10000
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
        self.on_finished()
                
    def cancel(self):
        QgsMessageLog.logMessage(
            'Task "{name}" was cancelled'.format(name=self.description()),
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

