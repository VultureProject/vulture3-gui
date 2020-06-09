#!/bin/sh
#
# This migration script patches the crontab RRD script to avoid
# timeout when trying to connect to non-running listener for mod_status stats
#
#
echo '#!/usr/bin/env /home/vlt-gui/env/bin/python2.7
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
__author__ = "Jeremie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = ""

import sys
import os
import urllib2
import ssl
import rrdtool
import re

# Django setup part
sys.path.append("/home/vlt-gui/vulture/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vulture.settings")
import django
django.setup()

from gui.models.system_settings import Cluster
from gui.models.application_settings import ListenAddress
from vulture_toolkit.network import net_utils

cluster = Cluster.objects.get()
node = cluster.get_current_node()
reg = re.compile(".*ReqPerSec: ([0-9.e\-+]+)\nBytesPerSec: ([0-9.e\-+]+)\nBytesPerReq: ([0-9.e\-+]+)\n", re.S)
done=list()

for listener in ListenAddress.objects.all():
    if listener.get_related_node() == node:

        key=listener.address.ip + str (listener.port)
        if key in done:
            continue
        done.append(key)

        """ Query only running listeners """
        status = net_utils.is_running(listener.address.ip, listener.port)
        if not status:
            continue

        req_rrd_path = "/var/db/rrdtools/reqpersec_{}.rrd".format(listener.id)
        if not os.path.exists(req_rrd_path):
            try:
                rrdtool.create(req_rrd_path,
                               "--start", "now", "--step", "60",
                               "DS:req_sec:GAUGE:600:U:U",
                               "DS:bytes_sec:GAUGE:600:U:U",
                               "DS:bytes_req:GAUGE:600:U:U",
                               "RRA:AVERAGE:0.5:1:288",
                               "RRA:AVERAGE:0.5:6:336",
                               "RRA:AVERAGE:0.5:24:360",
                               "RRA:AVERAGE:0.5:144:730"
                               )
            except Exception as e:
                print e
        worker_rrd_path = "/var/db/rrdtools/workers_{}.rrd".format(listener.id)
        if not os.path.exists(worker_rrd_path):
            try:
                rrdtool.create(worker_rrd_path,
                               "--start", "now", "--step", "60",
                               "DS:idle_workers:GAUGE:600:U:U",
                               "RRA:AVERAGE:0.5:1:288",
                               "RRA:AVERAGE:0.5:6:336",
                               "RRA:AVERAGE:0.5:24:360",
                               "RRA:AVERAGE:0.5:144:730"
                               )
            except Exception as e:
                print e
        # Retrieving informations
        proto = "http"
        if listener.ssl_profile:
            proto = "https"
        status_url = "{}://{}:{}/vulture-status?auto".format(proto, listener.address.ip, listener.port)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        request = urllib2.Request(status_url)
        response = urllib2.urlopen(request, context=ctx)
        status_info = response.read()
        response.close()
        res=reg.search(status_info)
        if res is not None:
            req_per_sec, bytes_per_sec, bytes_per_req = res.groups()
        else:
            print "problem with url {}://{}:{}/vulture-status?auto".format(proto, listener.address.ip, listener.port)
        # Updating RRD file
        rrdtool.update(req_rrd_path, "N:{}:{}:{}".format(req_per_sec, bytes_per_sec, bytes_per_req))

' > /home/vlt-gui/crontab/rrd-stats-minute/update_mod_status.minute
