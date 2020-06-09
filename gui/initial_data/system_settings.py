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

from django.utils.crypto import get_random_string


from gui.models.repository_settings import BaseAbstractRepository
from gui.models.repository_settings import MongoDBRepository
from gui.models.system_settings import (NTPSettings, Cluster, SystemSettings, GLOBALSettings, PFSettings, PfRules,
                                        LogAnalyserSettings, LogAnalyserRules)


class Import(object):

    def process(self):
        cluster = Cluster.objects.get()
        # Check if SystemSettings object is already created
        if not cluster.system_settings:
            cluster.system_settings = SystemSettings()
            cluster.save()

        # Creating Global Settings
        if not cluster.system_settings.global_settings:
            global_settings = GLOBALSettings()
            global_settings.owasp_crs_url = 'https://github.com/SpiderLabs/owasp-modsecurity-crs/archive/v3.0.2/master.zip'
            global_settings.trustwave_url = 'https://dashboard.modsecurity.org/rules/download/plain'
            global_settings.trustwave_user = ''
            global_settings.source_branch = ''
            global_settings.portal_cookie = get_random_string(8)
            global_settings.app_cookie = get_random_string(8)
            global_settings.public_token = get_random_string(16, 'abcdef0123456789')
            global_settings.redis_pwd = get_random_string(8)
            global_settings.city_name = "Paris"
            global_settings.latitude = 48.85661400000001
            global_settings.longitude = 2.3522219000000177
            global_settings.file_logrotate = "daily"
            global_settings.keep_logs = 30
            global_settings.log_rotate = 0
            global_settings.gui_timeout = 5
            global_settings.x_vlt_token = "X-Vlt-Token"
            cluster.system_settings.global_settings = global_settings
            cluster.save()
            print("Default Vulture settings successfully imported")

        # Creating NTP settings
        if not cluster.system_settings.ntp_settings:
            cluster.system_settings.ntp_settings = NTPSettings()
            cluster.save()
            print("Default NTP settings successfully imported")

        # DataBase LogAnalyzer
        if not cluster.system_settings.loganalyser_settings:
            cluster.system_settings.loganalyser_settings = LogAnalyserSettings()
            cluster.system_settings.loganalyser_settings.loganalyser_rules = []
            cluster.save()

            LOGANALYSER_DATABASES = [
                ("https://predator.vultureproject.org/ipsets/firehol_level1.netset", ["attacks"], "Vulture Firehol IPSET Level 1"),
            ]

            for rule in LOGANALYSER_DATABASES:
                cluster.system_settings.loganalyser_settings.loganalyser_rules.append(LogAnalyserRules(**{
                    'url': rule[0],
                    'description': rule[2],
                    'tags': ",".join(rule[1])
                }))

            cluster.save()


        node = cluster.get_current_node()
        if not node.system_settings.pf_settings:
            node.system_settings.pf_settings = PFSettings()
            node.system_settings.pf_settings.pf_rules.append (PfRules(action='pass',  log=True, direction='in', interface='any', protocol='tcp', port='80', rate='100/1', flags='flags S/SA keep state'))
            node.system_settings.pf_settings.pf_rules.append (PfRules(action='pass',  log=True, direction='in', interface='any', protocol='tcp', port='443', rate='100/1', flags='flags S/SA keep state'))
            node.system_settings.pf_settings.pf_rules.append (PfRules(action='pass',  log=True, direction='in', interface='any', protocol='tcp', port='8000', flags='flags S/SA keep state', comment='GUI admin - FIXME !'))
            node.system_settings.pf_settings.pf_rules.append (PfRules(action='pass',  log=True, direction='in', interface='any', protocol='tcp', port='22', rate='3/5', flags='flags S/SA keep state', comment='SSH admin - FIXME !'))
            node.system_settings.pf_settings.pf_rules.append (PfRules(action='pass',  log=True, direction='in', interface='any', protocol='carp', comment='Remove if carp is not used'))
            node.save(bootstrap=True)
            print("Default Packet Filter settings successfully imported")

        try:
            MongoDBRepository.objects.get(repo_name='Vulture Internal Database')
        except MongoDBRepository.DoesNotExist as e:

            """ If we are here, we are in the bootstraping of a Vulture Master node
                We don't want to call API at this time, so set bootstrap=True in save()
            """
            vlt_repo = MongoDBRepository()
            vlt_repo.is_internal = True
            vlt_repo.repo_name = 'Vulture Internal Database'
            # Fake values for host, port. Cuz fields are required but not used in internal repo
            vlt_repo.db_name = 'N/A'
            vlt_repo.db_host = 'N/A'
            vlt_repo.db_port = 9999
            vlt_repo.save(bootstrap=True)
            print("Vulture internal repository successfully imported")

        for repo in BaseAbstractRepository.get_data_repositories():
            if repo.is_internal:
                break

        cluster.system_settings.global_settings.logs_repository = repo.id
        cluster.save()