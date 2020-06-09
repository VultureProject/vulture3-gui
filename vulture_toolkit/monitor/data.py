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
__author__     = "Olivier de Régis"
__credits__    = []
__license__    = "GPLv3"
__version__    = "3.0.0"
__maintainer__ = "Vulture Project"
__email__      = "contact@vultureproject.org"
__doc__        = ''

import datetime

from gui.models.monitor_settings import Monitor
from gui.models.system_settings import Cluster


class MonitorData:
	def __init__(self):
		self.nodes = Cluster.objects.get().members

	def _prepare_aggregate(self, node, type_aggs):
		aggs = {
			'$match': {
				'node': node.id,
				'date': {
					'$gte': datetime.datetime.now() - datetime.timedelta(days=31),
					'$lte': datetime.datetime.now()
				}
			}
		}

		groups = {
			'$group': {
				'_id': {
					'year' : {'$year': "$date"},
					'month': {'$month': "$date"},
					'day'  : {'$dayOfMonth': "$date"},
				},
				'avg': {'$avg': '${}'.format(type_aggs)}
			}
		}

		sorts = {
			'$sort': {'_id': 1}
		}

		return aggs, groups, sorts

	def _format_date(self, date):
		return datetime.datetime.strptime("{}/{}/{}".format(date['day'], date['month'], date['year']), "%d/%m/%Y")

	def _format_results(self, data):
		date_start = datetime.datetime.now() - datetime.timedelta(days=31)

		tmp, results = {}, []
		for res in data:
			tmp[self._format_date(res['_id'])] = res['avg']

		for date in (date_start + datetime.timedelta(days=n) for n in range(32)):
			tmp_date = date.strptime(date.strftime('%d/%m/%Y'), '%d/%m/%Y')
			results.append((tmp_date, tmp.get(tmp_date, 0)))

		return results

	def get_average(self, data):
		results = {}
		for node in self.nodes:
			aggs, groups, sorts = self._prepare_aggregate(node, data)
			mon = list(Monitor.objects.aggregate(aggs, groups, sorts))
			results[node.name] = self._format_results(mon)
		return results
