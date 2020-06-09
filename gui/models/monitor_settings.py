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

from mongoengine import DateTimeField, DecimalField, DynamicDocument, IntField, ReferenceField, StringField

from gui.models.system_settings import Cluster
from vulture_toolkit.monitor.utils import MonitorUtils


class Monitor(DynamicDocument):
    """ Vulture Monitoring model representation

    """
    node = ReferenceField('Node', required=True)
    date = DateTimeField(default=datetime.datetime.now)
    cpu_percent = DecimalField()
    mem_percent = DecimalField()
    swap_percent = DecimalField()
    root_percent = DecimalField()
    var_percent = DecimalField()
    home_percent = DecimalField()
    users = IntField()
    nb_process = IntField()
    tot_bytes_sent = DecimalField()
    tot_bytes_recv = DecimalField()
    tot_packets_sent = DecimalField()
    tot_packets_recv = DecimalField()
    tot_errin = DecimalField()
    tot_errout = DecimalField()
    tot_dropin = DecimalField()
    tot_dropout = DecimalField()
    bytes_sent = DecimalField()
    bytes_recv = DecimalField()
    packets_sent = DecimalField()
    packets_recv = DecimalField()
    errin = DecimalField()
    errout = DecimalField()
    dropin = DecimalField()
    dropout = DecimalField()
    pf_state_entries = IntField()
    node_status = StringField()
    redis_mem_used = IntField()
    redis_mem_frag = DecimalField()

    meta = {
        'indexes': [
            "node",
            "date"
        ]
    }

    def add(self):
        node = Cluster.objects.get().get_current_node()
        last = Monitor.objects(node=node).order_by('-id').first()

        m = MonitorUtils(last)

        self.users = m.users
        self.cpu_percent = m.cpu_percent
        self.mem_percent = m.mem_percent
        self.swap_percent = m.swap_percent
        self.root_percent = m.root_percent
        self.var_percent = m.var_percent
        self.home_percent = m.home_percent
        self.nb_process = m.nb_process
        self.pf_state_entries = m.pf_state_entries
        self.node_status = m.node_process_status
        self.node = node

        redis = m.redis_stats
        self.redis_mem_used = redis['redis_mem_used']
        self.redis_mem_frag = redis['redis_mem_frag']

        network = m.network

        self.tot_bytes_sent = network['tot_bytes_sent']
        self.tot_bytes_recv = network['tot_bytes_recv']
        self.tot_packets_sent = network['tot_packets_sent']
        self.tot_packets_recv = network['tot_packets_recv']
        self.tot_errin = network['tot_errin']
        self.tot_errout = network['tot_errout']
        self.tot_dropin = network['tot_dropin']
        self.tot_dropout = network['tot_dropout']

        self.bytes_sent = network['bytes_sent']
        self.bytes_recv = network['bytes_recv']
        self.packets_sent = network['packets_sent']
        self.packets_recv = network['packets_recv']
        self.errin = network['errin']
        self.errout = network['errout']
        self.dropin = network['dropin']
        self.dropout = network['dropout']

        self.save()
