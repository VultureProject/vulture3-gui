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
__author__     = "Olivier de Régis"
__credits__    = []
__license__    = "GPLv3"
__version__    = "3.0.0"
__maintainer__ = "Vulture Project"
__email__      = "contact@vultureproject.org"
__doc__        = """This migration script update database for new mod sec operation
Move rules_set informations from modsec collection, to the app collection"""

import os
import re
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from bson.objectid import ObjectId
from gui.models.system_settings import Cluster

def update():
    cluster = Cluster.objects.get()
    node    = cluster.get_current_node()

    for app in node.get_applications():
        modsec_wl = ModSecRulesSet(name=app.name, type_rule="whitelist")
        modsec_wl.save()
        modsec_bl = ModSecRulesSet(name=app.name, type_rule="blacklist")
        modsec_bl.save()

        app.blacklist = modsec_bl
        app.whitelist = modsec_wl
        app.save()

        try:
            p = app.modsec_policy
        except:
            continue

        regexp = re.compile("[a-z&0-9]{24}")

        ## Check the id
        if regexp.match(str(app.modsec_policy.id)):
            ## Move the rules file from the disk and delete the old one
            os.system('mv /home/vlt-sys/Engine/conf/{}/modsec /home/vlt-sys/Engine/conf/modsec'.format(str(app.modsec_policy.id)))
            os.system('rm -r /home/vlt-sys/Engine/conf/{}'.format(str(app.modsec_policy.id)))

            ## Foreach app, get the rules_set and add them to the app, then save
            rules_set     = app.modsec_policy.rules_set
            app.rules_set = [ObjectId(rules.id) for rules in rules_set]
            app.save()


if __name__ == "__main__":
    update()