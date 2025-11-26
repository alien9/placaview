import random, requests, math
from time import sleep
from dateutil import parser
from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsTask)
from qgis.core import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtWebEngineWidgets import QWebEngineView
from qgis.PyQt.QtCore import *
from .tools import vt_bytes_to_geojson

MESSAGE_CATEGORY = 'PlacaView'

class SignsDownloader(QgsTask):
    layer:QgsVectorLayer
    interval=None,None
    filter=[]
    params=None
    work=0
    def __init__(self, key, layer, total, boundary, extents, from_, to_, filter_, params_=None):
        super().__init__("Downloading", QgsTask.CanCancel)
        self.duration = 1
        self.layer:QgsVectorLayer=layer
        self.boundary=boundary
        self.total = total
        self.work = 0
        self.extents=extents
        self.exception = None
        self.key=key
        self.result={}
        self.interval=(from_, to_)
        self.filter=filter_
        if params_:
            self.params=params_
        QgsMessageLog.logMessage('Instanced task "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage('Parameters "{}"'.format(
            str(params_)), MESSAGE_CATEGORY, Qgis.Info)

    def deg2num(self, lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (xtile, ytile)
    
    def num2deg(self, x, y, zoom):
        n = 2.0 ** zoom
        lon = x *360.0 / n -180.0      
        lat = math.atan(math.sinh((1- y / n * 2.0) *math.pi))
        return (lon, math.degrees(lat))
    
    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage('Parameters for task "{}"'.format(
            str(self.params)), MESSAGE_CATEGORY, Qgis.Info)
        
        nw, se=self.extents
        z=14        
        fields=self.layer.dataProvider().fields()
        boundary_features = list(self.boundary.getFeatures())
        idx = fields.indexOf('revision')
        
        revision=self.layer.maximumValue(idx)
        if revision is None:
            revision=0
        if str(revision)=='NULL':
            revision=0
        else:
            revision+=1
        QgsMessageLog.logMessage(f"Revision is {revision}", MESSAGE_CATEGORY, level=Qgis.Info)
        inserted_records=0
        updated_records=0
        downloaded_records=0
        self.layer.startEditing()        
        for x in range(nw[0], se[0]+1):
            for y in range(se[1], nw[1]+1):
                self.work += 1
                if self.isCanceled():
                    return False
                if self.total>0:
                    self.setProgress(100*self.work/self.total)
                
                if(self.params is not None): 
                    northwest=self.num2deg(x,y,z)
                    southeast=self.num2deg(x+1,y+1,z)
                    bbox=(northwest[0], southeast[1], southeast[0], northwest[1],)
                    url=f"https://graph.mapillary.com/map_features/?access_token={self.key}&fields=id,geometry,object_value,last_seen_at,first_seen_at&bbox={northwest[0]},{southeast[1]},{southeast[0]},{northwest[1]}"
                    if "object_values" in self.params:
                        url+=f'&object_values={self.params["object_values"]}'
                    if "start_first_seen_at" in self.params:
                        url+=f'&start_first_seen_at={self.params["start_first_seen_at"]}'
                    if "end_first_seen_at" in self.params:
                        url+=f'&end_first_seen_at={self.params["end_first_seen_at"]}'
                    if "start_last_seen_at" in self.params:
                        url+=f'&start_last_seen_at={self.params["start_last_seen_at"]}'
                    if "end_first_seen_at" in self.params:
                        url+=f'&end_last_seen_at={self.params["end_last_seen_at"]}'
                    r = requests.get(url)
                    if r.status_code == 403:
                        self.exception=403
                        return False
                    if self.isCanceled():
                        return False
                    features=r.json()
                    if "data" in features:
                        for point in features["data"]:
                            geometry = point.get("geometry")
                            if geometry.get("type") == "Point":
                                fet = QgsFeature()
                                fet.setFields(fields)
                                geo = QgsGeometry.fromPointXY(QgsPointXY(
                                    geometry.get("coordinates")[0], geometry.get("coordinates")[1]))
                                inside_boundary = False
                                for bf in boundary_features:
                                    if bf.geometry().contains(geo):
                                        inside_boundary = True

                                if inside_boundary:
                                    e=QgsFeatureRequest()
                                    e.setFilterExpression(f"\"id\"={point.get('id')}")
                                    fui=self.layer.dataProvider().getFeatures(e)
                                    feature=None
                                    for f in fui:
                                        feature = f
                                    if feature is not None:
                                        if str(feature["fid"])!='NULL':
                                            self.layer.dataProvider().enterUpdateMode()
                                            if feature["first_seen_at"] != parser.parse(point.get("first_seen_at")).timestamp() or feature["last_seen_at"] != parser.parse(point.get("last_seen_at")).timestamp() or feature["value"] != point.get("object_value"):
                                                updated_records+=1
                                            feature["first_seen_at"] = parser.parse(point.get(
                                                "first_seen_at")).timestamp()
                                            feature["last_seen_at"] = parser.parse(point.get(
                                                "last_seen_at")).timestamp()
                                            feature["value"] = point.get("object_value")
                                            feature["revision"]=revision
                                            self.layer.dataProvider().changeAttributeValues({
                                                int(feature["fid"]):{
                                                    fields.indexOf("value"):point.get("object_value"),
                                                    fields.indexOf("first_seen_at"):parser.parse(point.get(
                                                "first_seen_at")).timestamp(),
                                                    fields.indexOf("last_seen_at"):parser.parse(point.get(
                                                "last_seen_at")).timestamp(),
                                                    fields.indexOf("revision"):revision
                                                }
                                            })
                                            self.layer.dataProvider().leaveUpdateMode()
                                    else:
                                        QgsMessageLog.logMessage(f"FAILED for {point.get('id')}")
                                        fet.setGeometry(geo)
                                        fet["id"] = int(point.get("id"))
                                        fet["first_seen_at"] = parser.parse(point.get(
                                            "first_seen_at")).timestamp()
                                        fet["last_seen_at"] = parser.parse(point.get(
                                            "last_seen_at")).timestamp()
                                        fet["value"] = point.get("object_value")
                                        fet["revision"]=revision
                                        fet["value_code_face"] = f'symbols/{point.get("object_value")}.svg'
                                        try:
                                            self.layer.dataProvider().addFeatures([fet])
                                            inserted_records+=1
                                        except:
                                            QgsMessageLog.logMessage("cannot insert",MESSAGE_CATEGORY, level=Qgis.Info)

                else:
                    url = f"https://tiles.mapillary.com/maps/vtp/mly_map_feature_traffic_sign/2/{z}/{x}/{y}?access_token={self.key}"
                    r = requests.get(url)
                    if r.status_code == 403:
                        self.exception=403
                        return False
                    if self.isCanceled():
                        return False    
                    features = vt_bytes_to_geojson(r.content, x, y, z)
                    for f in features["features"]:
                        geometry = f.get("geometry")
                        if geometry.get("type") == "Point":
                            properties = f.get("properties")
                            fet = QgsFeature()
                            fet.setFields(fields)
                            geo = QgsGeometry.fromPointXY(QgsPointXY(
                                geometry.get("coordinates")[0], geometry.get("coordinates")[1]))
                            inside_boundary = False
                            for bf in boundary_features:
                                if bf.geometry().contains(geo):
                                    inside_boundary = True

                            if inside_boundary:
                                downloaded_records+=1
                                e=QgsFeatureRequest()
                                e.setFilterExpression(f"\"id\"={int(properties.get('id'))}")
                                fui=self.layer.dataProvider().getFeatures(e)
                                feature=None
                                i=0
                                for f in fui:
                                    feature = f
                                    i+=1
                                if i>0:
                                    self.layer.dataProvider().enterUpdateMode()
                                    if feature["first_seen_at"] != properties.get("first_seen_at") or feature["last_seen_at"] != properties.get("last_seen_at") or feature["value"] != properties.get("value"):
                                        updated_records+=1
                                    feature["first_seen_at"] = properties.get(
                                        "first_seen_at")
                                    feature["last_seen_at"] = properties.get(
                                        "last_seen_at")
                                    feature["value"] = properties.get("value")
                                    feature["revision"]=revision
                                    self.layer.dataProvider().changeAttributeValues({
                                        int(feature["fid"]):{
                                            fields.indexOf("value"):properties.get("value"),
                                            fields.indexOf("first_seen_at"):properties.get(
                                        "first_seen_at"),
                                            fields.indexOf("last_seen_at"):properties.get(
                                        "last_seen_at"),
                                            fields.indexOf("revision"):revision
                                        }
                                    })
                                    self.layer.dataProvider().leaveUpdateMode()
                                else:
                                    QgsMessageLog.logMessage(f"at {downloaded_records} an expression {properties.get('id')} not found: "+f"\"id\"={properties.get('id')}", MESSAGE_CATEGORY, level=Qgis.Info)
                                    fet.setGeometry(geo)
                                    fet["id"] = properties.get("id")
                                    fet["first_seen_at"] = properties.get(
                                        "first_seen_at")
                                    fet["last_seen_at"] = properties.get(
                                        "last_seen_at")
                                    fet["value"] = properties.get("value")
                                    fet["revision"]=revision
                                    fet["value_code_face"] = f'symbols/{properties.get("value")}.svg'
                                    try:
                                        self.layer.dataProvider().addFeatures([fet])
                                        inserted_records+=1
                                        QgsMessageLog.logMessage(f"inserted : {properties.get('id')}")
                                    except:
                                        QgsMessageLog.logMessage("cannot insert",MESSAGE_CATEGORY, level=Qgis.Info)
        self.layer.commitChanges()
        QgsMessageLog.logMessage(f"{downloaded_records} valid downloaded, {inserted_records}  inserted, {updated_records} updated",MESSAGE_CATEGORY, level=Qgis.Info)
        self.result={
            "downloaded": downloaded_records,
            "inserted": inserted_records,
            "updated": updated_records
        }
        return True

    def finished(self, result):        
        QgsMessageLog.logMessage(
            'Task "{name}" was finished'.format(name=self.description()),
            MESSAGE_CATEGORY, Qgis.Info)
                
    def cancel(self):
        QgsMessageLog.logMessage(
            'Task "{name}" was cancelled'.format(name=self.description()),
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

