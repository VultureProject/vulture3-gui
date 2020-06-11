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
__author__ = "Baptiste de Magnienville"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Initial data of ModDefender'

import os

from django.conf import settings

from vulture_toolkit.templates import tpl_utils


class Import(object):
    def process(self):
        defender_dir_path = settings.CONF_DIR + "defender/"
        if not os.path.exists(defender_dir_path):
            os.makedirs(defender_dir_path)
        core_rules_dst_path = defender_dir_path + "core.rules"

        tpl, path = tpl_utils.get_template('defender_core_rules')
        defender_core_rules = tpl.render(conf={'sql_warn': 1, 'sql_err': 2, 'sql_crit': 4,
                                               'rfi_warn': 1, 'rfi_err': 2, 'rfi_crit': 4,
                                               'traversal_warn': 1, 'traversal_err': 2, 'traversal_crit': 4,
                                               'xss_warn': 1, 'xss_err': 2, 'xss_crit': 4,
                                               'evade_warn': 1, 'evade_err': 2, 'evade_crit': 4,
                                               'upload_warn': 1, 'upload_err': 2, 'upload_crit': 4})

        with open(core_rules_dst_path, 'w') as f:
            f.write(defender_core_rules)

        print("ModDefender core rules generated")
