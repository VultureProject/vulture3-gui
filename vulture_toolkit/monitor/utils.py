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
__author__ = "Olivier de Régis"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = ''

import datetime
import json
import psutil
import subprocess

import redis

from gui.models.system_settings import Cluster


class MonitorUtils:
    def __init__(self, last=None):
        self.last = last

    @property
    def redis_stats(self):
        data = {
            'redis_mem_used': 0,
            'redis_mem_frag': 1,
        }
        try:
            redis_info = redis.StrictRedis(unix_socket_path='/var/db/redis/redis.sock', db=0, decode_responses=True).info()
            data = {
                'redis_mem_used': redis_info['used_memory'],
                'redis_mem_frag': redis_info['mem_fragmentation_ratio'],
            }
        except:
            pass

        return data


    @property
    def node_process_status(self):
        node = Cluster.objects.get().get_current_node()
        results = node.api_request("/api/supervision/process/")

        if results:
            return json.dumps (results)
        elif not results:
            """ Node has an error or is unreachable """
            return json.dumps ({
                'Applications': 'Error',
                'Listeners': 'Error',
                'Service ntpd': 'Error',
                'Service sshd': 'Error',
                'Service haproxy': 'Error',
                'Service mongod': 'Error',
                'Service redis': 'Error',
                'Service pf': 'Error',
                'Application Sessions': 'Error',
                'Portal Sessions': 'Error',
                'OAuth2 Sessions': 'Error',
                'Password Reset': 'Error',
                'Temporary Tokens': 'Error'
            })



    @property
    def boot_time(self):
        boot = psutil.boot_time()
        date = datetime.datetime.fromtimestamp(boot)
        date_now = datetime.datetime.now()
        delta = date_now - date

        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60

        return "{} days, {}h{}m{}s".format(delta.days, hours, minutes, seconds)

    @property
    def pf_state_entries(self):
        try:
            pf_stats = subprocess.Popen(
                ['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/sbin/pfctl', '-si'],
                stdout=subprocess.PIPE)
            state_entries = subprocess.Popen(['/usr/bin/grep', 'current entries'], stdin=pf_stats.stdout,
                                             stdout=subprocess.PIPE)
            return subprocess.Popen(['/usr/bin/awk', '{print $3}'], stdin=state_entries.stdout,
                                    stdout=subprocess.PIPE).stdout.read()
        except:
            return 0

    @property
    def root_percent(self):
        try:
            return psutil.disk_usage('/').percent
        except:
            return 0

    @property
    def home_percent(self):
        try:
            return psutil.disk_usage('/home').percent
        except:
            return 0

    @property
    def var_percent(self):
        try:
            return psutil.disk_usage('/var').percent
        except:
            return 0

    @property
    def cpu_percent(self):
        return psutil.cpu_percent(interval=1)

    @property
    def mem_percent(self):
        return psutil.virtual_memory().percent

    @property
    def users(self):
        return len(psutil.users())

    @property
    def network(self):
        netw = psutil.net_io_counters()

        data = {
            'tot_bytes_sent': netw.bytes_sent,
            'tot_bytes_recv': netw.bytes_recv,
            'tot_packets_sent': netw.packets_sent,
            'tot_packets_recv': netw.packets_recv,
            'tot_errin': netw.errin,
            'tot_errout': netw.errout,
            'tot_dropin': netw.dropin,
            'tot_dropout': netw.dropout
        }

        if not self.last:
            data.update({
                'bytes_sent': netw.bytes_sent,
                'bytes_recv': netw.bytes_recv,
                'packets_sent': netw.packets_sent,
                'packets_recv': netw.packets_recv,
                'errin': netw.errin,
                'errout': netw.errout,
                'dropin': netw.dropin,
                'dropout': netw.dropout
            })

        else:
            data.update({
                'bytes_sent': max(netw.bytes_sent - self.last.tot_bytes_sent, 0),
                'bytes_recv': max(netw.bytes_recv - self.last.tot_bytes_recv, 0),
                'packets_sent': max(netw.packets_sent - self.last.tot_packets_sent, 0),
                'packets_recv': max(netw.packets_recv - self.last.tot_packets_recv, 0),
                'errin': max(netw.errin - self.last.tot_errin, 0),
                'errout': max(netw.errout - self.last.tot_errout, 0),
                'dropin': max(netw.dropin - self.last.tot_dropin, 0),
                'dropout': max(netw.dropout - self.last.tot_dropout, 0)
            })

        return data

    @property
    def swap_percent(self):
        return psutil.swap_memory().percent

    @property
    def nb_process(self):
        return len(psutil.pids())
