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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant, pyqtSlot, QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QMessageBox, QProgressDialog, QProgressBar, QWidgetAction, QActionGroup
from qgis.core import QgsProject, QgsWkbTypes, QgsMapLayer, QgsVectorFileWriter, QgsAction
from qgis.core import QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsGeometry, QgsPoint
from qgis.core import QgsCategorizedSymbolRenderer
from qgis.PyQt import uic
from qgis.core import QgsStyle, QgsSymbol, QgsRendererCategory, QgsSvgMarkerSymbolLayer
from qgis.gui import QgsMapToolIdentifyFeature
from qgis.core import QgsSpatialIndex
from qgis.core import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWebKitWidgets import QWebView
from qgis.PyQt.QtCore import *
from .equidistance_buffer import EquidistanceBuffer

# Initialize Qt resources from file resources.py
from .resources import *
from .tools import *
from .signs_filter import SignsFilter
from .roads_selector import RoadsSelector
from .signs_selector import SignsSelector
# Import the code for the DockWidget
from .placa_view_dockwidget import PlacaViewDockWidget
import os.path
import os
import json
import requests
import math


class PlacaView:
    """QGIS Plugin Implementation."""
    boundary: QgsVectorLayer
    roads_layer: QgsVectorLayer
    signs_layer: QgsVectorLayer
    current_sign_images: object

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
        self.roads_layer = None
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

    def change_layer(self, layer):
        print("changed layer")
        print(layer)

    def deg2num(self, lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (xtile, ytile)

    def save_conf(self):
        with open(os.path.join(self.plugin_dir, "conf.json"), "w+") as fu:
            import json
            fu.write(json.dumps(self.conf))

    def set_conf(self, key, value):
        if not self.conf:
            self.load_conf()
        self.conf[key] = value
        self.save_conf()

    def load_conf(self):
        self.conf = {}
        con = os.path.join(self.plugin_dir, "conf.json")
        if os.path.isfile(con):
            with open(con, "r") as fu:
                self.conf = json.loads(fu.readlines().pop(0))
        if self.conf.get("boundary", False):
            self.boundary = self.get_boundary_by_name(
                self.conf.get("boundary"))
        if self.conf.get("roads", False):
            self.roads_layer = self.get_line_by_name(
                self.conf.get("roads"))
        self.roads_field_name = self.conf.get("roads_field_name", False)

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
            text="Set Roads",
            callback=self.ask_roads_layer,
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
        self.add_action(
            icon_path,
            text="Filter Signs",
            callback=self.load_signs_filter,
            parent=self.iface.mainWindow()
        )
        self.add_action(
            icon_path,
            text="Match Roads",
            callback=self.match_segment_roads,
            parent=self.iface.mainWindow()
        )
        for a in self.iface.attributesToolBar().actions():
            if a.statusTip() == 'Signs':
                self.iface.attributesToolBar().removeAction(a)

        self.click_tool = QAction(QIcon(os.path.join(
            self.plugin_dir, f"styles/symbols/regulatory--no-straight-through--g2.svg")), "Signs Database", self.iface.mainWindow())
        self.click_tool.setWhatsThis("Click on the map to edit")
        self.click_tool.setStatusTip("Signs")
        self.click_tool.setCheckable(True)
        self.click_tool.triggered.connect(self.start_select_features)

        actionList = self.iface.mapNavToolToolBar().actions()

        # Add actions from QGIS attributes toolbar (handling QWidgetActions)
        tmpActionList = self.iface.attributesToolBar().actions()
        for action in tmpActionList:
            if isinstance(action, QWidgetAction):
                actionList.extend(action.defaultWidget().actions())
            else:
                actionList.append(action)
        # ... add other toolbars' action lists...

        # Build a group with actions from actionList and add your own action
        group = QActionGroup(self.iface.mainWindow())
        group.setExclusive(True)
        for action in actionList:
            group.addAction(action)
            group.addAction(self.click_tool)

        # add toolbar button and menu item
        self.iface.attributesToolBar().addAction(self.click_tool)

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
            self.dockwidget.findChild(
                QPushButton, "pushButton_left").clicked.connect(self.page_down)
            self.dockwidget.findChild(
                QPushButton, "pushButton_right").clicked.connect(self.page_up)
            try:
                if self.roads_layer:
                    self.dockwidget.findChild(QLabel, "roads_label").setText(
                        f"Roads: {self.roads_layer.name()}")
            except:
                self.roads_layer=None
            try:
                if self.boundary:
                    self.dockwidget.findChild(QLabel, "boundary_label").setText(
                        f"Boundary: {self.boundary.name()}")
            except:
                self.boundary = None

    def ask_mapillary_key(self):
        text, ok = QInputDialog().getText(self.dockwidget, "Insert Key",
                                          "Mapillary Key:", QLineEdit.Normal,
                                          self.conf.get("mapillary_key", ""))
        self.conf["mapillary_key"] = text
        if ok:
            self.set_conf("mapillary_key", text)

    def ask_roads_layer(self):
        if not self.dockwidget:
            self.run()
        names = [layer.name() for layer in list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [
            QgsWkbTypes.LineString, QgsWkbTypes.MultiLineString] and x.dataProvider().storageType() in ["ESRI Shapefile", "GPKG"], QgsProject.instance().mapLayers().values()))]
        if not names:
            dlsg = QMessageBox(self.dockwidget)
            dlsg.setText("You need a LineString layer for roads")
            dlsg.exec()
            return
        layerindex = 0
        bs = QgsProject.instance().mapLayersByName(self.conf.get("roads"))
        if len(bs):
            self.roads_layer = bs[0]
            layername = self.roads_layer.name()
            if layername in names:
                layerindex = names.index(layername)
        fu = RoadsSelector(parent=self.iface.mainWindow(), roads=names, app=self, road=self.conf.get(
            "roads"), field=self.conf.get("roads_field_name"))
        fu.applyClicked.connect(self.set_roads_layer)
        fu.exec()

    def set_roads_layer(self, layer, field):
        self.roads_layer: QgsVectorLayer = self.get_line_by_name(layer)
        if self.dockwidget:
            self.dockwidget.findChild(QLabel, "roads_label").setText(
                f"Roads: {self.roads_layer.name()}")
        self.set_conf("roads", self.roads_layer.name())
        self.set_conf("roads_field_name", field)

    def ask_boundary_layer(self):
        if not self.dockwidget:
            self.run()
        names = [layer.name() for layer in list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [
            QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon], QgsProject.instance().mapLayers().values()))]
        if not names:
            dlsg = QMessageBox(self.dockwidget)
            dlsg.setText("You need a polygon layer for boundary")
            dlsg.exec()
            return
        layerindex = 0
        bs = QgsProject.instance().mapLayersByName(self.conf.get("boundary"))
        if len(bs):
            self.boundary = bs[0]
            layername = self.boundary.name()
            if layername in names:
                layerindex = names.index(layername)
        layer_name, ok = QInputDialog().getItem(self.dockwidget, "Choose Boundary",
                                                "Boundary Layer:", names,
                                                layerindex, False)
        if ok and layer_name:
            layers = list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon] and x.name(
            ) == layer_name, QgsProject.instance().mapLayers().values()))
            if layers:
                self.set_boundary_layer(layers[0])

    def set_boundary_layer(self, layer):
        self.boundary: QgsVectorLayer = layer
        if self.dockwidget:
            self.dockwidget.findChild(QLabel, "boundary_label").setText(
                f"Boundary: {layer.name()}")
        self.set_conf("boundary", layer.name())
        style = QgsStyle.defaultStyle()
        style.importXml(os.path.join(self.plugin_dir, "styles/boundary.xml"))
        renderer = QgsSingleSymbolRenderer(style.symbol("boundary"))
        layer.setRenderer(renderer)
        layer.triggerRepaint()

    def get_first_polygonal_layer(self):
        layers = list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [
                      QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon], QgsProject.instance().mapLayers().values()))
        if len(layers) == 1:
            self.set_boundary_layer(layers[0])

    def get_line_by_name(self, name):
        layers = list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [QgsWkbTypes.LineString, QgsWkbTypes.MultiLineString] and x.name(
        ) == name, QgsProject.instance().mapLayers().values()))
        if layers:
            return layers[0]

    def get_boundary_by_name(self, name):
        layers = list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon] and x.name(
        ) == name, QgsProject.instance().mapLayers().values()))
        if layers:
            return layers[0]

    def get_point_layer_by_name(self, name):
        layers = list(filter(lambda x: hasattr(x, 'fields') and x.wkbType() in [QgsWkbTypes.Point, QgsWkbTypes.MultiPoint] and x.name(
        ) == name, QgsProject.instance().mapLayers().values()))
        if layers:
            return layers[0]

    def download_signs(self):
        if not self.conf.get("boundary"):
            self.ask_boundary_layer()
        self.boundary = self.get_boundary_by_name(self.conf.get("boundary"))
        if not self.boundary:
            self.ask_boundary_layer()
        if not len(self.conf.get("mapillary_key", "")):
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
        # set a new message bar
        progressMessageBar = qgis.utils.iface.messageBar()
        progress = QProgressBar()
        # Maximum is set to 100, making it easy to work with percentage of completion
        progress.setMaximum(total_work)
        # pass the progress bar to the message Bar
        progressMessageBar.pushWidget(progress)
        boundary_features = list(self.boundary.getFeatures())
        work = 0
        for type in types:
            output = {"type": "FeatureCollection", "features": []}
            for x in range(nw[0], se[0]):
                print(x)
                for y in range(se[1], nw[1]):
                    work += 1
                    progress.setValue(work)
                    url = f"https://tiles.mapillary.com/maps/vtp/{type}/2/{z}/{x}/{y}?access_token={self.conf.get('mapillary_key')}"
                    r = requests.get(url)
                    if r.status_code == 403:
                        """Bad key"""
                        dlsg = QMessageBox(self.dockwidget)
                        dlsg.setText("Your Mapillary Key isn't valid")
                        dlsg.exec()
                        return
                    features = vt_bytes_to_geojson(r.content, x, y, z)
                    for f in features["features"]:
                        # {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [-58.347251415252686, -34.6904185494285]}, 'properties': {'first_seen_at': 1509570162000, 'id': 307511470929084, 'last_seen_at': 1509570162000, 'value': 'regulatory--no-heavy-goods-vehicles--g1'}}
                        geometry = f.get("geometry")
                        properties = f.get("properties")
                        if geometry.get("type") == "Point":
                            fet = QgsFeature()
                            fet.setFields(layer_provider.fields())
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
                                layer_provider.addFeatures([fet])
            layer.commitChanges()
            layer.updateExtents()
        progress.close()
        self.save_signs_layer()
        QgsProject.instance().removeMapLayer(layer.id())
        self.load_signs_layer()
        # qgis.utils.iface.messageBar().clearWidgets()

    def get_standard_attributes(self):
        return [QgsField("id",  QVariant.Double),
                QgsField("first_seen_at",  QVariant.Double),
                QgsField("last_seen_at",  QVariant.Double),
                QgsField("value",  QVariant.String),
                QgsField("road_id", QVariant.Double)
                ]

    def create_signals_vector_layer(self):
        vl = self.get_point_layer_by_name("traffic signs")
        if vl:
            return vl
        vl = QgsVectorLayer("Point", "traffic signs", "memory")
        pr = vl.dataProvider()
        # Enter editing mode
        vl.startEditing()
        # add fields
        pr.addAttributes(self.get_standard_attributes())
        QgsProject.instance().addMapLayer(vl)
        return vl

    def save_signs_layer(self):
        layer = self.get_point_layer_by_name("traffic signs")
        if not layer:
            dlsg = QMessageBox(self.dockwidget)
            dlsg.setText("Layer not Found")
            dlsg.exec()
            return
        title = QgsProject.instance().fileName()
        patty = os.path.join(QgsProject.instance().readPath(
            "./"), f"{title}_signs.gpkg")
        _writer = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer, patty, QgsCoordinateTransformContext(), QgsVectorFileWriter.SaveVectorOptions())

    def get_signs_layer(self):
        self.signs_layer = self.get_point_layer_by_name("traffic signs")
        if not self.signs_layer:
            self.load_signs_layer()
        return self.signs_layer

    def load_signs_layer(self):
        title = QgsProject.instance().fileName()
        l = self.get_point_layer_by_name("traffic signs")
        if l is not None:
            QgsProject.instance().removeMapLayer(l.id())
        uri = os.path.join(QgsProject.instance().readPath(
            "./"), f"{title}_signs.gpkg")
        if os.path.isfile(uri):
            print(f"loadring {uri}")
            self.signs_layer = QgsVectorLayer(uri, 'traffic signs', 'ogr')
            QgsProject.instance().addMapLayer(self.signs_layer)
            self.set_signs_style(self.read_filter(), self.signs_layer)
            mapTool = None
            mc = self.iface.mapCanvas()
            mapTool = QgsMapToolIdentifyFeature(mc)
            mapTool.setLayer(self.signs_layer)
            mc.setMapTool(mapTool)

    def get_signs_photo_layer(self):
        """ get or create the photo layer"""
        layer = self.get_point_layer_by_name("traffic signs images")
        if not layer:
            print("CREATING THE PHOTOS LAYER")
            layer = QgsVectorLayer("Point", "traffic signs images", "memory")
            pr = layer.dataProvider()
            # Enter editing mode
            layer.startEditing()
            # add fields
            pr.addAttributes([QgsField("id",  QVariant.String)])
            layer.updateFields()
            layer.endEditCommand()
            QgsProject.instance().addMapLayer(layer)
            self.iface.setActiveLayer(self.get_signs_layer())
        return layer

    def get_selected_sign_layer(self):
        """ get or create the selected sign layer"""
        print("GETTING SELECTED MARKERS")
        layer = self.get_point_layer_by_name("selected traffic sign")
        if not layer:
            layer= QgsVectorLayer("Point", "selected traffic sign", "memory")
            pr = layer.dataProvider()
            # Enter editing mode
            layer.startEditing()
            # add fields
            pr.addAttributes([QgsField("value",  QVariant.String)])
            layer.updateFields()
            QgsProject.instance().addMapLayer(layer)
            self.set_signs_style(self.read_filter(), layer, 10)
        return layer

    def set_signs_style(self, filter=[], layer=None, size=6):
        print("setting the style")
        signs_layer= self.get_point_layer_by_name("traffic signs")
        if layer is None:
            layer = self.get_point_layer_by_name("traffic signs")
        idx = signs_layer.fields().indexOf('value')
        values = list(signs_layer.uniqueValues(idx))
        categories = []
        for value in sorted(values):
            style = {
                "name": os.path.join(self.plugin_dir, f"styles/symbols/{value}.svg"),
                'size': size
            }
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.appendSymbolLayer(QgsSvgMarkerSymbolLayer.create(style))
            category = QgsRendererCategory(value, symbol, str(value))
            if value not in filter:
                category.setRenderState(False)
            categories.append(category)
        renderer = QgsCategorizedSymbolRenderer('value', categories)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

    def apply_filter(self, value):
        self.set_signs_style(value, self.read_filter())
        with open(os.path.join(self.plugin_dir, f"filter.txt"), "w+") as fu:
            for t in value:
                fu.write(f"{t}\n")

    def read_filter(self):
        value = []
        if os.path.isfile(os.path.join(self.plugin_dir, f"filter.txt")):
            with open(os.path.join(self.plugin_dir, f"filter.txt")) as fu:
                value = list(map(lambda x: x[0: -1], fu.readlines()))
        return value

    def load_signs_filter(self):
        fu = SignsFilter(parent=self.iface.mainWindow(),
                         filter=self.read_filter())
        fu.applyClicked.connect(self.apply_filter)
        fu.exec()

    def start_select_features(self):
        self.signs_layer = self.get_signs_layer()
        if not self.signs_layer:
            return
        self.iface.setActiveLayer(self.signs_layer)
        self.mapTool = SignsSelector(self.iface)
        self.mapTool.geomIdentified.connect(self.display_sign)
        self.mapTool.setLayer(self.signs_layer)
        self.iface.mapCanvas().setMapTool(self.mapTool)

    def show_image(self, image_id):
        self.image_id = image_id
        r = requests.get(
            f"https://graph.mapillary.com/{image_id}?access_token={self.conf.get('mapillary_key')}&fields=thumb_256_url")
        if r.status_code == 200:
            result = r.json()
            url = QUrl(result.get("thumb_256_url"))
            self.dockwidget.findChild(QWebView, "webView").load(url)
        image_layer = self.get_signs_photo_layer()
        categories = []
        idx = image_layer.fields().indexOf('id')
        values = list(image_layer.uniqueValues(idx))
        for value in values:
            symbol = QgsFillSymbol.createSimple(
                {'color': 'lime', 'outline_color': 'black'})
            if value == self.image_id:
                symbol = QgsMarkerSymbol.createSimple({'color': 'white'})
            else:
                symbol = QgsMarkerSymbol.createSimple({'color': 'black'})
            category = QgsRendererCategory(value, symbol, str(value))
            categories.append(category)
        renderer = QgsCategorizedSymbolRenderer('id', categories)
        image_layer.setRenderer(renderer)
        image_layer.triggerRepaint()

    def display_sign(self, *args, **kwargs):
        if not self.dockwidget:
            self.run()
        self.dockwidget.show()

        w: QWebView = self.dockwidget.findChild(QWebView, "webView")
        w.load(QUrl('https://www.google.ca/#q=pyqt'))
        w.setHtml("<html></html>")
        map_feature_id = int(args[1].attribute("id"))
        ss_layer = self.get_selected_sign_layer()
        fid = int(args[1].attribute("fid"))
        feature = self.get_signs_layer().getFeature(fid)
        ss_layer.dataProvider().truncate()
        ss_layer.startEditing()
        f = QgsFeature()
        f.setGeometry(feature.geometry())
        f.setAttributes([feature["value"]])
        ss_layer.addFeatures([f])
        ss_layer.commitChanges()
        ss_layer.triggerRepaint()
        ss_layer.updateExtents()
        ss_layer.triggerRepaint()
        url = f'https://graph.mapillary.com/{map_feature_id}?access_token={self.conf.get("mapillary_key")}&fields=images'
        fu = requests.get(
            url, headers={'Authorization': "OAuth "+self.conf.get("mapillary_key")})
        if fu.status_code == 200:
            photos = fu.json()
            image_layer = self.get_signs_photo_layer()
            image_layer.dataProvider().truncate()
            image_layer.triggerRepaint()
            if "images" in photos:
                for photo in photos.get("images", {}).get("data", []):
                    fet = QgsFeature()
                    geo = QgsGeometry.fromPointXY(QgsPointXY(
                        photo.get("geometry").get("coordinates")[0], photo.get("geometry").get("coordinates")[1]))
                    fet.setGeometry(geo)
                    fet.setAttributes([
                        str(int(photo.get("id")))
                    ])
                    image_layer.dataProvider().addFeatures([fet])
                    image_layer.triggerRepaint()
                if len(photos.get("images", {}).get("data", [])):
                    self.show_image(photos.get(
                        "images", {}).get("data", [])[0]["id"])
        self.current_sign_images = photos.get("images").get("data")
        self.current_sign_images_index = 0
        

    def page_up(self):
        self.current_sign_images_index += 1
        self.current_sign_images_index = self.current_sign_images_index % len(
            self.current_sign_images)
        self.show_image(
            self.current_sign_images[self.current_sign_images_index]["id"])

    def page_down(self):
        self.current_sign_images_index -= 1
        if self.current_sign_images_index < 0:
            self.current_sign_images_index = len(self.current_sign_images)-1
        self.show_image(
            self.current_sign_images[self.current_sign_images_index]["id"])

    def match_segment_roads(self):
        print("will match now")
        signs_layer: QgsVectorLayer = self.get_signs_layer()
        if not "roads" in [f.name() for f in signs_layer.fields()]:
            signs_layer.dataProvider().addAttributes(
                [QgsField("roads", QVariant.String)])
            signs_layer.updateFields()
        signs = signs_layer.selectedFeatureIds()
        if not len(signs):
            return
        boulder: QgsGeometry = EquidistanceBuffer().buffer(
            signs_layer.getFeature(signs[0]).geometry(), 35, signs_layer.crs()
        )
        roads_layer: QgsVectorLayer = self.get_line_by_name(
            self.conf.get("roads"))
        index = QgsSpatialIndex(roads_layer.getFeatures(
        ), flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
        for road in index.intersects(boulder.boundingBox()):
            print("found a road")
            print(road)
            if boulder.intersects(roads_layer.getFeature(road).geometry()):
                print(roads_layer.getFeature(road))
                print(roads_layer.getFeature(road).attribute(
                    self.conf.get("roads_field_name")))
