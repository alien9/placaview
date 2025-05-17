from urllib.parse import urlparse
import os, platform
import sys, time
import subprocess
from pathlib import Path
from qgis.core import QgsMessageLog

def install_requirements():
    if platform.uname().system=="Windows":
        QgsMessageLog.logMessage("Installing requirements for windows...")
        #definition of the bat file as as string
        #it will be equivalent to manually type these commands line by line
        batF="""@echo off
            call "->QGISPATH<-\\o4w_env.bat"
            call python -m pip install mapbox-vector-tile
            call python -m pip install vt2geojson
            call python -m pip install psycopg2
            call python -m pip install future
            
            call exit
            @echo on
            """
        qgispath = str(os.path.dirname(sys.executable))

        # here you replace the string ->QGISPATH<- with qgis path
        # so that the script is installation independant
        batF = batF.replace("->QGISPATH<-",qgispath)

        # and the string ->HOMEPATH<- with the path to your requirements.txt

        # then you write it to a .bat file and run it
        with open(f"{os.path.expanduser('~')}/INSTALL.bat","w") as f:
            f.write(batF)
        subprocess.run([f"{os.path.expanduser('~')}/INSTALL.bat"])
    else:
        import pip
        QgsMessageLog.logMessage("installing requirements")
        pip.main(["install","mapbox-vector-tile"])
        pip.main(["install","vt2geojson"])
        pip.main(["install","psycopg2"])
        pip.main(["install","future"])
        pip.main(["install", "PyQtWebEngine"])

try:
    from mapbox_vector_tile import decode
    from vt2geojson.features import Layer
    from qgis.PyQt.QtWebEngineWidgets import QWebEngineView
    import psycopg2
except (ModuleNotFoundError, ImportError):
    install_requirements()
    time.sleep(8)
    #import pip
    #pip.main(['install', 'mapbox-vector-tile'])
    #from mapbox_vector_tile import decode
try:
    from mapbox_vector_tile import decode
except (ModuleNotFoundError, ImportError):
    
    import pip
    pip.main(['install', 'mapbox-vector-tile'])
    from mapbox_vector_tile import decode
   
try:
    from vt2geojson.features import Layer
except (ModuleNotFoundError, ImportError):
    
    import pip
    pip.main(['install', 'vt2geojson'])
    from vt2geojson.features import Layer

def _is_url(uri: str) -> bool:
    """
    Checks if the uri is actually an url.
    :param uri: the string to check.
    :return: a boolean.
    """
    return urlparse(uri).scheme != ""


def vt_bytes_to_geojson(b_content: bytes, x: int, y: int, z: int, layer=None) -> dict:
    """
    Make a GeoJSON from bytes in the vector tiles format.
    :param b_content: the bytes to convert.
    :param x: tile x coordinate.
    :param y: tile y coordinate.
    :param z: tile z coordinate.
    :param layer: include only the specified layer.
    :return: a features collection (GeoJSON).
    """
    data = decode(b_content, y_coord_down=True)
    features_collections = [Layer(x=x, y=y, z=z, name=name, obj=layer_obj).toGeoJSON()
                            for name, layer_obj in data.items() if layer is None or name == layer]
    return {
        "type": "FeatureCollection",
        "features": [f for fc in features_collections for f in fc["features"]]
    }
