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
__doc__ = 'Initial data of ModSecRulesSet & ModSecRules'

import datetime

from django.conf import settings
from jinja2 import Environment, FileSystemLoader

from gui.models.modsec_settings import ModSecRulesSet, ModSecRules
from vulture_toolkit.templates.template_configuration import FREEBSD_TEMPLATES_CONF


class Import(object):
    def create_wl(self, rs_name, date_rule, rule_name, rule_tpl):
        try:
            ruleset = ModSecRulesSet.objects.get(name=rs_name)
        except ModSecRulesSet.DoesNotExist as e:
            ruleset = ModSecRulesSet(name=rs_name, type_rule='vulture')
            ruleset.save()

        rule = ModSecRules.objects.filter(name=rule_name, rs=ruleset).first()
        if not rule:
            rule = ModSecRules(name=rule_name, rs=ruleset, is_enabled=True, date_rule=date_rule)

        env = Environment(loader=FileSystemLoader(settings.SVC_TEMPLATES_DIR + 'def_wl/'))
        if settings.OS == 'FreeBSD':
            conf = FREEBSD_TEMPLATES_CONF
        tpl_conf = conf.get(rule_tpl)
        tpl = env.get_template(tpl_conf['tpl_name'])

        rule.rule_content = tpl.render()
        rule.save()

        ruleset.conf = ruleset.get_conf()
        ruleset.save()

        print("Defender whitelist '" + str(rs_name) + "' successfully imported")

    def process(self):
        wl = [
            ["Dokuwiki WL", "Defender Dokuwiki whitelist", 'defender_wl_dokuwiki'],
            ["Drupal WL", "Defender Drupal whitelist", 'defender_wl_drupal'],
            ["Etherpad Lite WL", "Defender Etherpad Lite whitelist", 'defender_wl_etherpad-lite'],
            ["Iris WL", "Defender Iris whitelist", 'defender_wl_iris'],
            ["Owncloud WL", "Defender Owncloud whitelist", 'defender_wl_owncloud'],
            ["Rutorrent WL", "Defender Rutorrent whitelist", 'defender_wl_rutorrent'],
            ["Wordpress WL", "Defender Wordpress whitelist", 'defender_wl_wordpress'],
            ["Wordpress Minimal WL", "Defender Wordpress Minimal whitelist", 'defender_wl_wordpress-minimal'],
            ["Zerobin WL", "Defender Zerobin whitelist", 'defender_wl_zerobin'],
              ]

        date_rule = datetime.datetime.strptime('2017-04-28T16:00:00', "%Y-%m-%dT%H:%M:%S")
        for rs in wl:
            self.create_wl(rs[0], date_rule, rs[1], rs[2])

        print("Defender Whitelists imported")