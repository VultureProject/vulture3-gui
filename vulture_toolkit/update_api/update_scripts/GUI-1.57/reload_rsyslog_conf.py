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
__doc__ = """This migration script reload Rsyslog configuration"""

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from gui.models.modlog_settings import ModLog
from gui.models.repository_settings import MongoDBRepository, SyslogRepository
from gui.models.system_settings import Cluster
from vulture_toolkit.system.syslog import Rsyslogd

from bson import ObjectId


if __name__ == '__main__':

    cluster = Cluster.objects.get()
    global_settings = cluster.system_settings.global_settings

    conf_logrotate = {
        'apps': False,
        'system': global_settings,
    }

    node = cluster.get_current_node()
    apps = node.get_applications()
    data_repo_logs = ModLog.objects.filter(repository_type='data')
    data_syslogrepo_logs = ModLog.objects.filter()
    data_repo_apps = list()
    learning_apps = []

    internal_mongo = MongoDBRepository.objects.get(is_internal=True)
    uri_learning = "mongodb://{}/?replicaset=Vulture&ssl=true".format(internal_mongo.replica_list)
    ssl_ca = "/var/db/mongodb/ca.pem"
    ssl_cert = "/var/db/mongodb/mongod.pem"

    """ Looking for local applications with a configured data repository """
    for app in sorted(apps, key=lambda x: x.name):

        conf_logrotate['apps'] = True

        if app.log_custom in data_repo_logs:
            app.log_custom.file_logrotate = "daily"
            app.log_custom.keep_logs = 30

            """ Build MongoDB Connection URI """
            if app.log_custom.repository.is_internal:
                app.uristr = "mongodb://"+app.log_custom.repository.replica_list+'/?replicaset=Vulture&ssl=true'
                app.ssl_ca = "/var/db/mongodb/ca.pem"
                app.ssl_cert = "/var/db/mongodb/mongod.pem"
            elif app.log_custom.repository.type_uri == 'mongodb':
                if app.log_custom.repository.db_user and app.log_custom.repository.db_password:
                    app.uristr = "mongodb://"+app.log_custom.repository.db_user+":" + \
                                 app.log_custom.repository.db_password+"@"+app.log_custom.repository.db_host+':' + \
                                 str(app.log_custom.repository.db_port)+'/'
                else:
                    app.uristr = "mongodb://"+app.log_custom.repository.db_host+':' + \
                                 str(app.log_custom.repository.db_port)+'/'

                opt = list()
                if app.log_custom.repository.replicaset:
                    opt.append('replicaset='+str(app.log_custom.repository.replicaset))
                if app.log_custom.repository.db_client_cert:
                    opt.append('ssl=true')

                    certificate_path, chain_path = app.log_custom.repository.db_client_cert.write_MongoCert()
                    app.ssl_ca = chain_path
                    app.ssl_cert = certificate_path

                if '?' in app.uristr:
                    app.uristr = app.uristr+"&".join(opt)
                elif opt:
                    app.uristr = app.uristr+"?"+"&".join(opt)
                    app.uristr.replace("?&", "?")

            elif app.log_custom.repository.type_uri == "elasticsearch":
                app.es_dateformat = app.log_custom.repository.es_dateformat.replace("%Y", "%timegenerated:::date-year%")
                app.es_dateformat = app.es_dateformat.replace("%m", "%timegenerated:::date-month%")
                app.es_dateformat = app.es_dateformat.replace("%d", "%timegenerated:::date-day%")
                app.es_dateformat = app.es_dateformat.replace("%H", "%timegenerated:::date-hour%")
                app.es_dateformat = app.es_dateformat.replace("%M", "%timegenerated:::date-minute%")
                app.es_dateformat = app.es_dateformat.replace("%S", "%timegenerated:::date-second%")

        """ Pass SYSLOG Repository Instance to Application """
        if app.log_custom in data_syslogrepo_logs and app.log_custom.syslog_repository is not None:
            try:
                syslog_repo = SyslogRepository.objects.with_id(ObjectId(app.log_custom.syslog_repository))
                app.syslog_repo = syslog_repo
            except:
                pass

        if app.learning:
            app.learning_uristr = uri_learning
            app.learning_ssl_ca = ssl_ca
            app.learning_ssl_cert = ssl_cert
            learning_apps.append(app)

        data_repo_apps.append(app)

    try:
        pf_settings = None
        if node.system_settings.pf_settings.repository_type == 'data':
            pf_settings = node.system_settings.pf_settings.repository
            """ Build MongoDB Connection URI """
            if pf_settings.is_internal:
                pf_settings.uristr = "mongodb://"+pf_settings.replica_list+'/?replicaset=Vulture&ssl=true'
                pf_settings.ssl_ca = "/var/db/mongodb/ca.pem"
                pf_settings.ssl_cert = "/var/db/mongodb/mongod.pem"
            elif pf_settings.type_uri == 'mongodb':
                if pf_settings.db_user and pf_settings.db_password:
                    pf_settings.uristr = "mongodb://"+pf_settings.db_user+":"+pf_settings.db_password+"@" + \
                                         pf_settings.db_host+':'+str(pf_settings.db_port)+'/'
                else:
                    pf_settings.uristr = "mongodb://"+pf_settings.db_host+':'+str(pf_settings.db_port)+'/'

                opt = list()
                if pf_settings.replicaset:
                    pf_settings.append('replicaset='+str(pf_settings.replicaset))
                if pf_settings.db_client_cert:
                    opt.append('ssl=true')

                    certificate_path, chain_path = pf_settings.db_client_cert.write_MongoCert()
                    app.ssl_ca = chain_path
                    app.ssl_cert = certificate_path

                if '?' in app.uristr:
                    app.uristr = app.uristr+"&".join(opt)
                else:
                    app.uristr = app.uristr+"?"+"&".join(opt)
                    app.uristr.replace("?&", "?")

            elif pf_settings.type_uri == "elasticsearch":
                pf_settings.es_dateformat = pf_settings.es_dateformat.replace("%Y","%timegenerated:::date-year%")
                pf_settings.es_dateformat = pf_settings.es_dateformat.replace("%m","%timegenerated:::date-month%")
                pf_settings.es_dateformat = pf_settings.es_dateformat.replace("%d","%timegenerated:::date-day%")
                pf_settings.es_dateformat = pf_settings.es_dateformat.replace("%H","%timegenerated:::date-hour%")
                pf_settings.es_dateformat = pf_settings.es_dateformat.replace("%M","%timegenerated:::date-minute%")
                pf_settings.es_dateformat = pf_settings.es_dateformat.replace("%S","%timegenerated:::date-second%")
    except:
        pf_settings = None

    try:
        syslog_pf_repo = SyslogRepository.objects.with_id(ObjectId(node.system_settings.pf_settings.syslog_repository))
    except Exception as e:
        syslog_pf_repo = False

    syslog_conf = {
        'pf_syslog': syslog_pf_repo,
        'pf_settings': pf_settings,
        'app_list': data_repo_apps,
        'learning_apps': learning_apps
    }

    """ Now dealing with Rsyslogd configuration """
    rsyslogd = Rsyslogd()
    new_conf = rsyslogd.conf_has_changed(syslog_conf)
    if new_conf:
        if rsyslogd.write_configuration(None, None, new_conf):
            status = rsyslogd.restart_service()
            print "[+] Rsyslog service restarted: {}".format(status)

    print("[*] New rsyslog configuration applied.")
