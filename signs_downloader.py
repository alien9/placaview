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
    def __init__(self, key, layer, total, boundary, extents):
        super().__init__("Downloading", QgsTask.CanCancel)
        self.duration = 1
        self.layer=layer
        self.boundary=boundary
        self.total = total
        self.work = 0
        self.extents=extents
        self.exception = None
        self.key=key
        self.result=[]
        QgsMessageLog.logMessage('Instanced task "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)

    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(
            self.description()), MESSAGE_CATEGORY, Qgis.Info)
        nw, se=self.extents
        z=14        
        fields=self.layer.dataProvider().fields()
        boundary_features = list(self.boundary.getFeatures())
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
                            fet.setGeometry(geo)
                            fet["id"] = properties.get("id")
                            fet["first_seen_at"] = properties.get(
                                "first_seen_at")
                            fet["last_seen_at"] = properties.get(
                                "last_seen_at")
                            fet["value"] = properties.get("value")
                            self.layer.dataProvider().addFeatures([fet])
                            self.layer.commitChanges()
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

