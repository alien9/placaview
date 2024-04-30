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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDialog, QInputDialog, QLineEdit
from qgis.core import QgsProject, QgsWkbTypes
# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .placa_view_dockwidget import PlacaViewDockWidget
import os.path, os,json

class PlacaView:
    """QGIS Plugin Implementation."""

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

        #load mapillary key
        self.mapillary_key=""
        self.conf={}
        pat = os.path.join(self.plugin_dir, "mapillary_key.txt")
        if os.path.isfile(pat):
            with open(pat, "r") as fu:
                self.mapillary_key=fu.readlines().pop(0)
        con = os.path.join(self.plugin_dir, "conf.json")
        if os.path.isfile(con):
            with open(con, "r") as fu:
                self.conf=json.loads(fu.readlines().pop(0))
                print(f"cargo {self.conf}")

        # initialize locale
        loc=QSettings().value('locale/userLocale')
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

        #print "** INITIALIZING PlacaView"

        self.pluginIsActive = False
        self.dockwidget = None


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

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
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
            callback=self.ask_boundary_leyer,
            parent=self.iface.mainWindow()            
        )
        self.add_action(
            icon_path,
            text="Download Signs",
            callback=self.download_signs,
            parent=self.iface.mainWindow()            
        )

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING PlacaView"

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

        #print "** UNLOAD PlacaView"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Road Sign Database'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING PlacaView"

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
            
    def ask_mapillary_key(self):
        print("will add the key")
        text, ok = QInputDialog().getText(self.dockwidget, "Insert Key",
                                "Mapillary Key:", QLineEdit.Normal,
                                self.mapillary_key)
        self.conf["mapillary_key"]=text
        if ok:
            with open(os.path.join(self.plugin_dir, "mapillary_key.txt"), "w+") as fu:
                fu.write(text)
        if ok:
            with open(os.path.join(self.plugin_dir, "app.json"), "w+") as fu:
                import json
                fu.write(json.dumps(self.conf))
                
    def ask_boundary_leyer(self):
        from qgis.PyQt.QtWidgets import QDialog, QLabel, QDialogButtonBox, QMessageBox
        names = [layer.name() for layer in list(filter(lambda x: x.wkbType() in [QgsWkbTypes.Polygon,QgsWkbTypes.MultiPolygon], QgsProject.instance().mapLayers().values()))]
        if not names:
            dlsg=QMessageBox(self.dockwidget)
            dlsg.setText("You need a polygon layer for boundary")
            dlsg.exec()
            return
        layer, ok = QInputDialog().getItem(self.dockwidget, "Choose Boundary",
                                            "Boundary Layer:", names,
                                            0, False)
        if ok and layer:
            self.boundary=layer

    def download_signs(self):
        print("Download signs.")