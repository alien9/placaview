
from qgis.core import (Qgis, QgsApplication, QgsMessageLog, QgsTask)
import requests


class SignDataDownloader(QgsTask):
    key = None
    image_id = None
    result = None
    road_id: int = None
    road_name: str = None
    datatype: str = "imagery"

    def run(self):
        try:
            if self.datatype == "imagery":
                url = f"https://graph.mapillary.com/{self.image_id}?access_token={self.key}&fields={self.fields}"
            if self.datatype == "geometry":
                url = f'https://graph.mapillary.com/{self.image_id}/detections?access_token={self.key}&fields=geometry,value'
            r = requests.get(url)
            if r.status_code == 200:
                self.result = r.json()
                return True
            
            return False
        except Exception as e:
            
            
            self.exception = e
            return False

    def __init__(self, *args, **kwargs):
        super().__init__("Downloading", QgsTask.CanCancel)
        self.key = kwargs.get('mapillary_key')
        self.image_id = kwargs.get('image').get("id")
        self.fields = kwargs.get('fields')
        if "datatype" in kwargs:
            self.datatype = kwargs.get("datatype")