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


FREEBSD_TEMPLATES_CONF = {
    'ntpd': {'tpl_name': 'ntp.conf', 'tpl_path': '/etc/ntp.conf'},
    'dns': {'tpl_name': 'dns.conf', 'tpl_path': '/etc/resolv.conf'},
    'smtp': {'tpl_name': 'ssmtp.conf', 'tpl_path': '/usr/local/etc/ssmtp/ssmtp.conf'},
    'mail': {'tpl_name': 'mailer.conf', 'tpl_path': '/etc/mail/mailer.conf'},
    'mongodb': {'tpl_name': 'mongodb.conf', 'tpl_path': '/usr/local/etc/mongodb.conf'},
    'elasticsearch-access': {'tpl_name': 'elasticsearch-access.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'elasticsearch-pf': {'tpl_name': 'elasticsearch-pf.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'elasticsearch-vulture': {'tpl_name': 'elasticsearch-vulture.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'elasticsearch-diagnostic': {'tpl_name': 'elasticsearch-diagnostic.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'rsyslogd': {'tpl_name': 'rsyslog.conf', 'tpl_path': '/usr/local/etc/rsyslog.d/rsyslog.conf'},
    'loganalyzer': {'tpl_name': 'loganalyzer.json', 'tpl_path': '/usr/local/etc/loganalyzer.json'},
    'rc.conf.local': {'tpl_name': 'rc.conf.local', 'tpl_path': '/etc/rc.conf.local'},
    'kerberos': {'tpl_name': 'krb5.conf', 'tpl_path': '/etc/krb5.conf'},
    'pf': {'tpl_name': 'pf.conf', 'tpl_path': '/usr/local/etc/pf.conf'},
    'gui': {'tpl_name': 'gui_httpd.conf', 'tpl_path': '/home/vlt-sys/Engine/conf/gui-httpd.conf'},
    'portal': {'tpl_name': 'portal_httpd.conf', 'tpl_path': '/home/vlt-sys/Engine/conf/portal-httpd.conf'},
    'redis': {'tpl_name': 'redis.conf', 'tpl_path': '/usr/local/etc/redis.conf'},
    'logrotate': {'tpl_name': 'logrotate.conf', 'tpl_path': '/usr/local/etc/logrotate.d/vulture.conf'},
    'sentinel': {'tpl_name': 'sentinel.conf', 'tpl_path': '/usr/local/etc/sentinel.conf'},
    'vulture_httpd': {'tpl_name': 'vulture_httpd.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'vulture_application': {'tpl_name': 'vulture_application.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'vulture_sub_application': {'tpl_name': 'vulture_sub_application.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'vulture_svm2': {'tpl_name': 'vulture_svm2.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'vulture_svm3': {'tpl_name': 'vulture_svm3.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'vulture_svm4': {'tpl_name': 'vulture_svm4.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'vulture_svm5': {'tpl_name': 'vulture_svm5.conf', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'defender_core_rules': {'tpl_name': 'defender_core.rules', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/'},
    'defender_wl_dokuwiki': {'tpl_name': 'dokuwiki.rules', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/def_wl/'},
    'defender_wl_drupal': {'tpl_name': 'drupal.rules', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/def_wl/'},
    'defender_wl_etherpad-lite': {'tpl_name': 'etherpad-lite.rules', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/def_wl/'},
    'defender_wl_iris': {'tpl_name': 'iris.rules', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/def_wl/'},
    'defender_wl_owncloud': {'tpl_name': 'owncloud.rules', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/def_wl/'},
    'defender_wl_rutorrent': {'tpl_name': 'rutorrent.rules', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/def_wl/'},
    'defender_wl_wordpress': {'tpl_name': 'wordpress.rules', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/def_wl/'},
    'defender_wl_wordpress-minimal': {'tpl_name': 'wordpress-minimal.rules', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/def_wl/'},
    'defender_wl_zerobin': {'tpl_name': 'zerobin.rules', 'tpl_path': '/home/vlt-gui/vulture/vulture_toolkit/templates/def_wl/'},
    'vlthaproxy': {'tpl_name': 'vlthaproxy.conf', 'tpl_path': '/usr/local/etc/vlthaproxy.conf'},
    'strongswan': {'tpl_name': 'strongswan.conf', 'tpl_path': '/usr/local/etc/strongswan.conf'},
    'ipsec': {'tpl_name': 'ipsec.conf', 'tpl_path': '/usr/local/etc/ipsec.conf'},
    'ipsec-secrets': {'tpl_name': 'ipsec.secrets', 'tpl_path': '/usr/local/etc/ipsec.secrets'},
    'zabbix_agentd': {'tpl_name': 'zabbix_agentd.conf', 'tpl_path': '/usr/local/etc/zabbix4/zabbix_agentd.conf'},
}
