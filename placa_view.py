# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PlacaView
                                 A QGIS plugin
 This plugin manages road signs
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-04-26
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Tiago Barufi
        email                : barufi@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsField, QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint


# Initialize Qt resources from file resources.py
from .resources import *
from .tools import *

# Import the code for the DockWidget
from .placa_view_dockwidget import PlacaViewDockWidget
import os.path
import os
import json
import requests
import math


class PlacaView:
    """QGIS Plugin Implementation."""
    boundary: QgsMapLayer

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # load mapillary key
        self.mapillary_key = ""
        self.boundary = None
        self.conf = {}
        pat = os.path.join(self.plugin_dir, "mapillary_key.txt")
        if os.path.isfile(pat):
            with open(pat, "r") as fu:
                self.mapillary_key = fu.readlines().pop(0)
        self.load_conf()

        # initialize locale
        loc = QSettings().value('locale/userLocale')
        if loc:
            locale = loc[0:2]
            locale_path = os.path.join(
                self.plugin_dir,
                'i18n',
                'PlacaView_{}.qm'.format(locale))

            if os.path.exists(locale_path):
                self.translator = QTranslator()
                self.translator.load(locale_path)
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Road Sign Database')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'PlacaView')
        if self.toolbar:
            self.toolbar.setObjectName(u'PlacaView')
        self.pluginIsActive = False
        self.dockwidget = None

    def deg2num(self, lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (xtile, ytile)

    def save_conf(self):
        print("ewill save now", self.conf)
        with open(os.path.join(self.plugin_dir, "conf.json"), "w+") as fu:
            import json
            fu.write(json.dumps(self.conf))

    def set_conf(self, key, value):
        print("settinhg conf..;")
        if not self.conf:
            print("conf does not exist")
            self.load_conf()
        print(self.conf)
        self.conf[key] = value
        print("ll save now", self.conf)
        self.save_conf()

    def load_conf(self):
        from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem
        self.conf = {}
        con = os.path.join(self.plugin_dir, "conf.json")
        print("loading...", con)
        if os.path.isfile(con):
            with open(con, "r") as fu:
                self.conf = json.loads(fu.readlines().pop(0))
        if self.conf.get("boundary", False):
            self.boundary = self.get_boundary_by_name(
                self.conf.get("boundary"))

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PlacaView', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabledinitGui
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/placa_view/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Manage Road Signs'),
            callback=self.run,
            parent=self.iface.mainWindow())
        self.add_action(
            icon_path,
            text="Configure Mapillary Key",
            callback=self.ask_mapillary_key,
            parent=self.iface.mainWindow()
        )
        self.add_action(
            icon_path,
            text="Set Boundary",
            callback=self.ask_boundary_layer,
            parent=self.iface.mainWindow()
        )
        self.add_action(
            icon_path,
            text="Download Signs",
            callback=self.download_signs,
            parent=self.iface.mainWindow()
        )
        self.add_action(
            icon_path,
            text="Save Signs",
            callback=self.save_signs_layer,
            parent=self.iface.mainWindow()
        )
        self.add_action(
            icon_path,
            text="Load Signs",
            callback=self.load_signs_layer,
            parent=self.iface.mainWindow()
        )

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING PlacaView"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD PlacaView"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Road Sign Database'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # print "** STARTING PlacaView"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = PlacaViewDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
            self.get_first_polygonal_layer()

    def ask_mapillary_key(self):
        print("will add the key")
        text, ok = QInputDialog().getText(self.dockwidget, "Insert Key",
                                          "Mapillary Key:", QLineEdit.Normal,
                                          self.conf.get("mapillary_key", ""))
        self.conf["mapillary_key"] = text
        if ok:
            self.set_conf("mapillary_key", text)

    def ask_boundary_layer(self):
        from qgis.PyQt.QtWidgets import QDialog, QLabel, QDialogButtonBox, QMessageBox
        if not self.dockwidget:
            self.run()
        names = [layer.name() for layer in list(filter(lambda x: x.wkbType() in [
            QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon], QgsProject.instance().mapLayers().values()))]
        if not names:
            dlsg = QMessageBox(self.dockwidget)
            dlsg.setText("You need a polygon layer for boundary")
            dlsg.exec()
            return
        layerindex = 0
        if self.boundary:
            layername = self.boundary.name()
            if layername in names:
                layerindex = names.index(layername)
        layer_name, ok = QInputDialog().getItem(self.dockwidget, "Choose Boundary",
                                                "Boundary Layer:", names,
                                                layerindex, False)
        if ok and layer_name:
            layers = list(filter(lambda x: x.wkbType() in [QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon] and x.name(
            ) == layer_name, QgsProject.instance().mapLayers().values()))
            if layers:
                self.set_boundary_layer(layers[0])

    def set_boundary_layer(self, layer):
        self.boundary = layer
        if self.dockwidget:
            self.dockwidget.findChild(QLabel, "boundary_label").setText(
                f"Boundary: {layer.name()}")
        self.set_conf("boundary", layer.name())

    def get_first_polygonal_layer(self):
        layers = list(filter(lambda x: x.wkbType() in [
                      QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon], QgsProject.instance().mapLayers().values()))
        if len(layers) == 1:
            self.set_boundary_layer(layers[0])

    def get_boundary_by_name(self, name):
        layers = list(filter(lambda x: x.wkbType() in [QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon] and x.name(
        ) == name, QgsProject.instance().mapLayers().values()))
        if layers:
            return layers[0]

    def get_point_layer_by_name(self, name):
        layers = list(filter(lambda x: x.wkbType() in [QgsWkbTypes.Point, QgsWkbTypes.MultiPoint] and x.name(
        ) == name, QgsProject.instance().mapLayers().values()))
        if layers:
            return layers[0]

    def download_signs(self):
        if not self.conf.get("boundary"):
            self.ask_boundary_layer()
        self.boundary=self.get_boundary_by_name(self.conf.get("boundary"))
        if not self.boundary:
            self.ask_boundary_layer()
        if not len(self.mapillary_key):
            self.ask_mapillary_key()
        if not self.boundary:
            return
        sourceCrs = self.boundary.crs()
        tr = QgsCoordinateTransform(
            sourceCrs, QgsCoordinateReferenceSystem.fromEpsgId(4326), QgsProject.instance())
        trans = tr.transformBoundingBox(self.boundary.extent())
        z = 14
        nw = self.deg2num(trans.yMinimum(), trans.xMinimum(), z)
        se = self.deg2num(trans.yMaximum(), trans.xMaximum(), z)
        total_work = (nw[0]-se[0])*(se[1] - nw[1])
        # types = ["mly1_computed_public","mly_map_feature_point","mly_map_feature_traffic_sign","mly1_computed_public","mly1_public"]
        types = ["mly_map_feature_traffic_sign"]
        layer = self.create_signals_vector_layer()
        layer.startEditing()
        layer_provider = layer.dataProvider()
        import qgis
        qgis.utils.iface.messageBar().clearWidgets() 
        #set a new message bar
        progressMessageBar = qgis.utils.iface.messageBar()
        progress = QProgressBar()
        #Maximum is set to 100, making it easy to work with percentage of completion
        progress.setMaximum(total_work) 
        #pass the progress bar to the message Bar
        progressMessageBar.pushWidget(progress)
        boundary_features=list(self.boundary.getFeatures())
        work=0
        for type in types:
            output = {"type": "FeatureCollection", "features": []}
            for x in range(nw[0], se[0]):
                for y in range(se[1], nw[1]):
                    work+=1
                    progress.setValue(work)
                    print(type, x, y)
                    url = f"https://tiles.mapillary.com/maps/vtp/{type}/2/{z}/{x}/{y}?access_token={self.conf.get('mapillary_key')}"
                    print(url)
                    r = requests.get(url)
                    if r.status_code == 403:
                        """Bad key"""
                        dlsg = QMessageBox(self.dockwidget)
                        dlsg.setText("Your Mapillary Key isn't valid")
                        dlsg.exec()
                        return
                    features = vt_bytes_to_geojson(r.content, x, y, z)
                    print(features)
                    for f in features["features"]:
                        # {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [-58.347251415252686, -34.6904185494285]}, 'properties': {'first_seen_at': 1509570162000, 'id': 307511470929084, 'last_seen_at': 1509570162000, 'value': 'regulatory--no-heavy-goods-vehicles--g1'}}
                        geometry = f.get("geometry")
                        properties = f.get("properties")
                        if geometry.get("type") == "Point":
                            fet = QgsFeature()
                            geo=QgsGeometry.fromPointXY(QgsPointXY(
                                geometry.get("coordinates")[0], geometry.get("coordinates")[1]))
                            inside_boundary=False
                            
                            for bf in boundary_features:
                                if bf.geometry().contains(geo):
                                    inside_boundary=True
                            if inside_boundary:
                                print("INSIDED")
                                fet.setGeometry(geo)

                                fet.setAttributes([
                                    properties.get("id"),
                                    properties.get("first_seen_at"),
                                    properties.get("last_seen_at"),
                                    properties.get("value")
                                ])
                                layer_provider.addFeatures([fet])
                            else:
                                print("no good")
            layer.commitChanges()
            layer.updateExtents()
        progress.close()
        qgis.utils.iface.messageBar().clearWidgets()  

    def create_signals_vector_layer(self):
        vl = self.get_point_layer_by_name("traffic signs")
        if vl:
            return vl
        vl = QgsVectorLayer("Point", "traffic signs", "memory")
        pr = vl.dataProvider()
        # Enter editing mode
        vl.startEditing()
        # add fields
        pr.addAttributes([QgsField("id",  QVariant.Double),
                          QgsField("first_seen_at",  QVariant.Double),
                          QgsField("last_seen_at",  QVariant.Double),
                          QgsField("value",  QVariant.String)
                          ])
        QgsProject.instance().addMapLayer(vl)
        return vl

    def save_signs_layer(self):
        layer=self.get_point_layer_by_name("traffic signs")
        print(QgsProject.instance().readPath("./"))
        patty=os.path.join(QgsProject.instance().readPath("./"), "signs_ensured.gpkg")
        _writer = QgsVectorFileWriter.writeAsVectorFormatV3(layer, patty, QgsCoordinateTransformContext(),QgsVectorFileWriter.SaveVectorOptions())

    def load_signs_layer(self):
        uri=os.path.join(QgsProject.instance().readPath("./"), "signs_ensured.gpkg")
        layer = QgsVectorLayer(uri, 'traffic signs', 'ogr')
        QgsProject.instance().addMapLayer(layer)
