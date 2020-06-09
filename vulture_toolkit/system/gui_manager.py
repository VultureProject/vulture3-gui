#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from vulture_toolkit.system.sys_utils import write_in_file
from vulture_toolkit.templates import tpl_utils


class GuiManager(object):
    """ Class used to handle some operation on Vulture Graphic User Interface.

    """
    @staticmethod
    def build_configuration_files(listen_ip=None):
        """ Check if Vulture GUI Apache configuration file has changed.
        If changes are detected, a new one is writed.

        :return:
        """
        try:
            # Looking for listen IP from DB data
            if not listen_ip:
                from gui.models.system_settings import Cluster
                cluster = Cluster.objects.get()
                node = cluster.get_current_node()
                mngt_listener = node.get_management_listener()
                listen_ip = mngt_listener.ip
            parameters = {'listen_ip': listen_ip}
            tpl, path = tpl_utils.get_template('gui')
            conf = tpl.render(conf=parameters)
            try:
                f = open(path, 'r')
                orig_conf = f.read()
            except IOError:
                orig_conf = None
            # Configuration file differs => writing new version
            if orig_conf != conf:
                write_in_file(path, conf)
            tpl, path = tpl_utils.get_template('portal')
            conf = tpl.render(conf={})
            try:
                f = open(path, 'r')
                orig_conf = f.read()
            except IOError:
                orig_conf = None
            # Configuration file differs => writing new version
            if orig_conf != conf:
                write_in_file(path, conf)
            return True
        except Exception as e:
            return False
