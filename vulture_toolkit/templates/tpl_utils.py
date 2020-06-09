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
__doc__ = 'Template Toolkit'

import os
import sys

sys.path.append("/home/vlt-gui/vulture/vulture/")
os.environ['DJANGO_SETTINGS_MODULE'] = 'vulture.settings'
from django.conf import settings
from jinja2 import Environment, FileSystemLoader
from vulture_toolkit.templates.template_configuration import FREEBSD_TEMPLATES_CONF


def get_template(tpl_name):
    """ Get template configuration file

    :param tpl_name: name of template
    :returns: jinja2.environment.Template variable and path of tpl
    """
    # Loading configuration parameters
    if settings.OS == 'FreeBSD':
        conf = FREEBSD_TEMPLATES_CONF

    tpl_conf = conf.get(tpl_name)
    if tpl_conf is not None:
        env = Environment(loader=FileSystemLoader(settings.SVC_TEMPLATES_DIR))
        tpl = env.get_template(tpl_conf['tpl_name'])
        return tpl, tpl_conf['tpl_path']
    else:
        raise Exception("Unable to find template " + tpl_name)

