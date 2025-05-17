# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'barufi@gmail.com'
__date__ = '2024-04-26'
__copyright__ = 'Copyright 2024, Tiago Barufi'
import sys
sys.path.append('../')
import unittest, os, inspect
#from .qgis_interface import QgsInterface
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface
from .utilities import get_qgis_app
from placa_view import *
from qgis.PyQt.QtWidgets import *

QGIS_APP = get_qgis_app()

# dummy instance to replace qgis.utils.iface
class QgisInterfaceDummy(object):
    def __getattr__(self, name):
        # return an function that accepts any arguments and does nothing
        def dummy(*args, **kwargs):
            return None
        return dummy


class PlacaViewResourcesTest(unittest.TestCase):
    """Test rerources work."""
    
    def setUp(self):
        """Runs before each test."""
        app=get_qgis_app()
        self.placaview=PlacaView(QgisInterfaceDummy())
        
        
        self.placaview.run()
    def tearDown(self):
        """Runs after each test."""
        pass
        #self.app=None
        #self.dockwidget = None

    def test_icon_png(self):
        """Test we can click OK. Create a Quico"""
        path = ':/plugins/PlacaView/icon.png'
        icon = QIcon(path)
        self.assertFalse(icon.isNull())
        
    def test_ask_mapillary_key(self):
        """Testing if the dialog is created"""
        self.assertIsNone(self.placaview.dockwidget.findChildren(QInputDialog))
        self.placaview.ask_mapillary_key()
        
        pass
        #self.dockwidget.dockwidget.ask_mapillary_key()
        #self.assertFalse(1==2)

if __name__ == "__main__":
    suite = unittest.makeSuite(PlacaViewResourcesTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)



