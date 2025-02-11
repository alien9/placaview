import random, requests
from time import sleep

from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsTask)
from qgis.core import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtCore import *
from .tools import vt_bytes_to_geojson

MESSAGE_CATEGORY = 'Download task'

class SignsDownloader(QgsTask):
    layer:QgsVectorLayer
    interval=None,None
    filter=[]
    def __init__(self, key, layer, total, boundary, extents, from_, to_, filter_):
        super().__init__("Downloading", QgsTask.CanCancel)
        self.duration = 1
        self.layer:QgsVectorLayer=layer
        self.boundary=boundary
        self.total = total
        self.work = 0
        self.extents=extents
        self.exception = None
        self.key=key
        self.result=[]
        self.interval=(from_, to_)
        self.filter=filter_
        QgsMessageLog.logMessage('Instanced task "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)

    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)
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
        self.layer.startEditing()        
        for x in range(nw[0], se[0]):
            for y in range(se[1], nw[1]):
                self.work += 1
                if self.isCanceled():
                    return False
                self.setProgress(100*self.work/self.total)
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
                            e=QgsFeatureRequest()
                            e.setFilterExpression(f"\"id\"='{properties.get('id')}'")
                            fui=self.layer.dataProvider().getFeatures(e)
                            feature=None
                            for f in fui:
                                feature = f
                            if feature is not None:
                                if str(feature["fid"])!='NULL':
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
                                except:
                                    QgsMessageLog.logMessage("cannot insert",MESSAGE_CATEGORY, level=Qgis.Info)
        self.layer.commitChanges()
        QgsMessageLog.logMessage(f"{inserted_records}  inserted, {updated_records} updated",MESSAGE_CATEGORY, level=Qgis.Info)
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

