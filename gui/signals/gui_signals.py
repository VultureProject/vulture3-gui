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
__author__ = "Florian Hagniel, Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django signals'

import django.dispatch
from bson.objectid import ObjectId
from mongoengine import Q

# Registering signal
app_modified = django.dispatch.Signal()
log_modified = django.dispatch.Signal()
repo_modified = django.dispatch.Signal()
listener_modified = django.dispatch.Signal()
node_modified = django.dispatch.Signal()
config_modified = django.dispatch.Signal()
krb5_modified = django.dispatch.Signal()
cluster_modified = django.dispatch.Signal()

def check_config_changes (sender, id, **kwargs):
    """ Receiver of config_modified signal.
    This checks if the Vulture's Apache configuration files needs to be refreshed

    :param sender:
    :param kwargs:
    :return:
    """

    from gui.models.application_settings import Application, ListenAddress
    from gui.models.modssl_settings import ModSSL
    from gui.models.rewrite_settings import Rewrite

    """ According to sender name, find Applications using the sender's Class """
    if sender.__name__ == "ModLog":
        app_list = Application.objects.filter(log_custom=ObjectId(id))

    elif sender.__name__ == "ModAccess":
        app_list = Application.objects.filter(access_mode=ObjectId(id))

    elif sender.__name__ == 'portalTemplate':
        listeners, tmp = [], []
        for app in Application.objects.filter(template=ObjectId(id)):
            for l in app.listeners:
                if "{}:{}".format(l.address.ip, l.port) not in tmp:
                    l.is_up2date = False
                    l.save()
                    tmp.append("{}:{}".format(l.address.ip, l.port))

        return None

    elif sender.__name__ == "SSLCertificate" or sender.__name__ == "ModSSL":
        if sender.__name__ == "SSLCertificate":
            ssl_profile = ModSSL.objects.filter(certificate=ObjectId(id))
            listeners = list()
            for profile in ssl_profile:
                ls = ListenAddress.objects.filter(ssl_profile=profile)
                for l in ls:
                    if l not in listeners:
                        listeners.append(l)
        else:
            listeners = ListenAddress.objects.filter(ssl_profile=ObjectId(id))

        """ Job's done: check listeners """
        done = list()
        for listener in listeners:
            key = listener.address.ip + ':' + listener.port
            if key not in done:
                print("Dealing with listener " + key)
                listener.need_restart()
                done.append(key)

        return None

    elif sender.__name__ == "ModSec":
        app_list = Application.objects.filter(modsec_policy=ObjectId(id))

    elif sender.__name__ == "ModSecRulesSet":
        app_list = Application.objects.filter(Q(rules_set=ObjectId(id)) or Q(wlbl=ObjectId(id)))

    elif sender.__name__ == "ProxyBalancer":
        app_list = Application.objects.filter(proxy_balancer=ObjectId(id))

    elif sender.__name__ == "Rewrite":
        app_list = None
        try:
            app_list = Rewrite.objects.get(id=ObjectId(id)).application
        except:
            pass
        """ This is a rule that apply to all applications """
        if not app_list:
            app_list = Application.objects()

    elif sender.__name__ == "Worker":
        app_list = Application.objects.filter(worker=ObjectId(id))

    elif sender.__name__ == "Cluster":
        app_list = Application.objects.all()

    else:
        print("Signal::check_config_changes(): Sender is unknown: " + str(sender.__name__))
        return None

    done = list()
    for app in app_list:
        for listener in app.listeners:
            key = listener.address.ip+':'+str(listener.port)
            if key not in done:
                print("Dealing with listener " + key)
                listener.need_restart()
                done.append(key)

def check_logging_changes(sender, **kwargs):
    """ Receiver of app_modified signal. Make an API call to all Cluster's
    member. This call check if rsyslogd configuration file has changed

    :param sender:
    :param kwargs:
    :return:
    """

    from gui.models.system_settings import Cluster
    try:
        cluster = Cluster.objects.get()
        cluster.api_request("/api/logs/management/")
    except Cluster.DoesNotExist:
        # Exception raised during bootstrap process, we can ignore it
        pass

def refresh_rcconf(sender, **kwargs):
    """ Make an API call to all Cluster's
    member. This call check if rc.conf need update

    :param sender:
    :param kwargs:
    :return:
    """
    from gui.models.system_settings import Cluster
    try:
        cluster = Cluster.objects.get()
        cluster.api_request("/api/cluster/management/conf/")
    except Cluster.DoesNotExist:
        # Exception raised during bootstrap process, we can ignore it
        pass


def refresh_krb5conf(sender, **kwargs):
    """ Make an API call to all Cluster's
    member. This call check if krb5.conf need update
    :param sender:
    :param kwargs:
    :return:
    """
    from gui.models.system_settings import Cluster
    try:
        cluster = Cluster.objects.get()
        cluster.api_request("/api/cluster/management/conf/krb5/")
    except Cluster.DoesNotExist:
        # Exception raised during bootstrap process, we can ignore it
        pass


# Connecting signals
app_modified.connect(check_logging_changes)
log_modified.connect(check_logging_changes)
repo_modified.connect(check_logging_changes)
listener_modified.connect(refresh_rcconf)
node_modified.connect(refresh_rcconf)
node_modified.connect(check_logging_changes)
config_modified.connect(check_config_changes)
cluster_modified.connect(check_logging_changes)
krb5_modified.connect(refresh_krb5conf)