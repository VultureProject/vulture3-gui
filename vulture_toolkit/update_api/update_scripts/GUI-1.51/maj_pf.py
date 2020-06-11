#!/home/vlt-gui/env/bin/python2.7
# coding:utf-8

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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = """This migration script update Packet Filter rules"""

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from gui.models.system_settings import Cluster, PfRules

if __name__ == '__main__':
    svg_pf_filename = '/home/vlt-gui/pf.conf.old'

    cluster = Cluster.objects.get()
    node = cluster.get_current_node()

    # Save old configuration - if not already done
    pf_settings = node.system_settings.pf_settings
    if not os.path.exists(svg_pf_filename):
        with open(svg_pf_filename, 'w') as f:
            f.write(str(pf_settings.pf_rules_text))

    # Add default rules
    pf_settings.pf_rules.append(
        PfRules(action='pass', log=True, direction='in', interface='any', protocol='tcp', port='80', rate='100/1',
                flags='flags S/SA keep state'))
    pf_settings.pf_rules.append(
        PfRules(action='pass', log=True, direction='in', interface='any', protocol='tcp', port='443', rate='100/1',
                flags='flags S/SA keep state'))
    pf_settings.pf_rules.append(
        PfRules(action='pass', log=True, direction='in', interface='any', protocol='tcp', port='8000',
                flags='flags S/SA keep state', comment='GUI admin - FIXME !'))
    pf_settings.pf_rules.append(
        PfRules(action='pass', log=True, direction='in', interface='any', protocol='tcp', port='22', rate='3/5',
                flags='flags S/SA keep state', comment='SSH admin - FIXME !'))
    pf_settings.pf_rules.append(
        PfRules(action='pass', log=True, direction='in', interface='any', protocol='carp',
                comment='Remove if carp is not used'))

    # And replace text config
    pf_settings.pf_rules_text = """

#Never remove this line
{{rule}}

"""
    # And add newly added attributes with default value
    if not hasattr(pf_settings, 'pf_limit_states'):
        pf_settings.pf_limit_states = 100000
    if not hasattr(pf_settings, 'pf_limit_frags'):
        pf_settings.pf_limit_frags = 25000
    if not hasattr(pf_settings, 'pf_limit_src'):
        pf_settings.pf_limit_src = 50000

    node.system_settings.pf_settings = pf_settings
    node.save(bootstrap=True)

    print("New Packet Filter settings successfully added")
