#!/usr/bin/python
#-*- coding: utf-8 -*-
"""This file is part of Vulture 3.

Vulture 3 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Vulture 3 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vulture 3.  If not, see http://www.gnu.org/licenses/.
"""
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = ''

from gui.models.system_settings import Cluster, Version
from vulture_toolkit.update_api.engine_updater import EngineUpdater
from vulture_toolkit.update_api.gui_updater import GUIUpdater


class Import(object):

    def process(self):
        try:
            cluster = Cluster.objects.get()
            node = cluster.get_current_node()
            if not node.version:
                version = Version()
                gui_updater = GUIUpdater()
                engine_updater = EngineUpdater()
                version.gui_version = gui_updater.current_version
                version.gui_last_version = gui_updater.current_version
                version.engine_version = engine_updater.current_version
                version.engine_last_version = engine_updater.current_version
                node.version = version
                node.save()
                print("Node version successfully imported")
        except Exception as e:
            print("An error has occurred during version import, error: {}".format(e))