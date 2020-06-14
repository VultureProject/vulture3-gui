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
__author__ = "Olivier de Régis"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = ''


import datetime
import pytz
import re
import logging
from vulture_toolkit.log.reporting_dict import type_of_dict
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from calendar import monthrange
logger = logging.getLogger('debug')

class BaseLog(object):

    def __init__(self, **kwargs):
        """ Abstract class, we can't instantiate it

        """
        raise NotImplementedError()

    def search(self, collection_name, params):
        raise NotImplementedError("Use of authenticate method of BaseLog "
                                  "object is not allowed. You have to redefine "
                                  "it")

    def merge_aggregations(self, aggregation, previous_results):
        """ Public method, allow to merge a previous aggregation with a new one (either mongo or els)
            only called when multiple repos are used for reporting. Look over new results to find results with the
             same name in the previous results. If found, merge values according to function's type (sum, avg, concat
             etc...) and replace previous result or append merged result in previous results

        :param aggregation: new results of an aggregation
        :param previous_results: previous results of an aggregation
        :returns: merged results
        """
        results = {}

        for function, values in aggregation.items():
            results[function] = previous_results[function]
            if type_of_dict(function, "date_based") and type_of_dict(function, "multiple_series"):
                for key, value in values.items():
                    try:
                        previous_dict = previous_results[function][key]
                        for entry in value:
                            prev_result_dict = filter(lambda item: item['name'] == entry['name'],  previous_dict)
                            if prev_result_dict:
                                index = previous_dict.index(prev_result_dict[0])

                                if type_of_dict(function, "average"):
                                    prev_result_dict = {"name" : entry['name'], "value" : (entry['value'] + prev_result_dict[0]['value'])/2}
                                else:
                                    prev_result_dict = {"name": entry['name'], "value": prev_result_dict[0]['value'] + entry['value']}

                                previous_dict[index] = prev_result_dict

                            else:
                                previous_dict.append(entry)
                        previous_results[function][key] = previous_dict
                        previous_results[function][key].sort(key=lambda x:x["name"])
                    except:
                        previous_results[function][key] = value
                        pass

            else:
                for entry in values:
                    prev_result_dict = filter(lambda item: item['name'] == entry['name'],  previous_results[function])
                    if prev_result_dict:
                        index = previous_results[function].index(prev_result_dict[0])

                        if type_of_dict(function, "average"):
                            prev_result_dict = {"name" : entry['name'], "value" : (entry['value'] + prev_result_dict[0]['value'])/2}

                        elif function == "reputation_tags":
                            for entry_ip in entry["ips"]:
                                previous_ip = filter(lambda item: item['ip'] == entry_ip['ip'],  prev_result_dict[0]["ips"])
                                if previous_ip:
                                    index_ip = prev_result_dict[0]["ips"].index(previous_ip[0])
                                    previous_ip = {"ip": entry_ip["ip"], "value": (entry_ip['value'] + previous_ip[0]["value"])}
                                    prev_result_dict[0]["ips"][index_ip] = previous_ip

                                else:
                                    prev_result_dict[0]["ips"].append(entry_ip)

                            prev_result_dict[0]["ips"].sort(key=lambda x:x["value"], reverse=True)
                            prev_result_dict = {"name": entry['name'], "value": prev_result_dict[0]['value'] + entry['value'], "ips": prev_result_dict[0]['ips'][:20]}

                        elif type_of_dict(function, "multiple_series"):
                            for sub_entry in entry["value"]:
                                previous_sub_entry = filter(lambda item: item['name'] == sub_entry['name'],  prev_result_dict[0]["value"])
                                if previous_sub_entry:
                                    index_sub_entry = prev_result_dict[0]["value"].index(previous_sub_entry[0])
                                    previous_sub_entry = {"name": sub_entry["name"], "value": (sub_entry['value'] + previous_sub_entry[0]["value"])}
                                    prev_result_dict[0]["value"][index_sub_entry] = previous_sub_entry

                                else:
                                    prev_result_dict[0]["value"].append(sub_entry)

                            prev_result_dict = {"name": entry['name'], "value": prev_result_dict[0]['value']}

                        else:
                            prev_result_dict = {"name": entry['name'], "value": prev_result_dict[0]['value'] + entry['value']}

                        previous_results[function][index] = prev_result_dict

                    else:
                        previous_results[function].append(entry)


                if type_of_dict(function, "date_based"):
                    previous_results[function].sort(key=lambda x:x["name"])

                elif type_of_dict(function, "order_count"):
                    previous_results[function].sort(key=lambda x:x["value"], reverse=True)

        return previous_results

    def _get_date_range(self, startDate, endDate):
        """ Private method, return a date range depending on a start date, an end date and
        the date_accuracy used by the request (either minutes, hours, days or months)

        :param startDate: start datetime object
        :param endDate: end datetime object
        :returns: date_range to iter on
        """
        round_accuracy = 1 if endDate == self.endDate else 0

        if self.date_accuracy == 'minute':
            endDate = endDate.replace(second=0, microsecond=0)
            startDate = startDate.replace(second=0, microsecond=0)
            delta = relativedelta(endDate, startDate)
            delta_range =  delta.minutes + round_accuracy
            return (startDate + relativedelta(minutes=n) for n in range(0,delta_range))

        elif self.date_accuracy == 'hour':
            endDate = endDate.replace(minute=0, second=0, microsecond=0)
            startDate = startDate.replace(minute=0, second=0, microsecond=0)
            delta = relativedelta(endDate, startDate)
            delta_range =  delta.hours + round_accuracy
            return (startDate + relativedelta(hours=n) for n in range(0,delta_range))

        elif self.date_accuracy == 'day':
            endDate = endDate.replace(hour=0, minute=0, second=0, microsecond=0)
            startDate = startDate.replace(hour=0, minute=0, second=0, microsecond=0)
            delta = relativedelta(endDate, startDate)
            delta_range = 0
            if delta.months >= 1:
                delta_range += monthrange(startDate.year, startDate.month)[1]
            delta_range += delta.days + round_accuracy
            return (startDate + relativedelta(days=n) for n in range(0,delta_range))

        elif self.date_accuracy == 'month':
            endDate = endDate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            startDate = startDate.replace(day=1, minute=0, second=0, microsecond=0)
            delta = relativedelta(endDate, startDate)
            delta_range = delta.months + round_accuracy
            return (startDate + relativedelta(months=n) for n in range(0,delta_range))

        else:
            return (startDate + relativedelta(days=n) for n in range(0,0))


    def _set_date_accuracy(self):
        """ Private method, sets date_accuracy for BaseLog according to delta requested by user """
        if self.delta.total_seconds() <= 7200:
            self.date_accuracy = 'minute'

        elif self.delta.days <= 2:
            self.date_accuracy = 'hour'

        elif self.delta.days <= 62:
            self.date_accuracy = 'day'

        else:
            self.date_accuracy = 'month'


    def fill_data(self, results):
        """ Public method, format data obtained after mongo or els aggregate, format timestamps according
        to request's timedelta (mongo only) and also add new entries with 0 as value between aggregated data for
        reporting accuracy.

        :param data: data obtained after aggregation
        :param function: function name of current report_dicts
        :return: array of filled results
        """
        filled_results = results.copy()

        for function, values in results.items():
            if type_of_dict(function, "multiple_series") and type_of_dict(function, "date_based"):
                filled_series = {}
                for key, value in values.items():
                    data = value
                    series = []
                    previous_date = self.startDate
                    for row in data:
                        date = row['name']
                        date_range = self._get_date_range(previous_date, date)
                        for single_date in date_range:
                            if single_date != previous_date or (previous_date == self.startDate and single_date != previous_date):
                                inter_result = {"name" : single_date, "value" : 0}
                                series.append(inter_result.copy())

                        series.append(row)
                        previous_date = date

                        if row == data[-1]:
                            end_date_range = self._get_date_range(date, self.endDate)
                            for single_date in end_date_range:
                                if single_date != previous_date:
                                    last_result = {"name" : single_date, "value" : 0}
                                    series.append(last_result.copy())

                    filled_series[key] = series

                filled_results[function] = filled_series

            elif type_of_dict(function, "date_based"):
                data = results[function]
                series = []
                previous_date = self.startDate
                for row in data:
                    date = row['name']
                    date_range = self._get_date_range(previous_date, date)

                    for single_date in date_range:
                        if single_date != previous_date or (previous_date == self.startDate and single_date != previous_date):
                            inter_result = {"name" : single_date, "value" : 0}
                            series.append(inter_result.copy())

                    series.append(row)
                    previous_date = date

                    if row == data[-1]:
                        end_date_range = self._get_date_range(date, self.endDate)
                        for single_date in end_date_range:
                            if single_date != previous_date:
                                last_result = {"name" : single_date, "value" : 0}
                                series.append(last_result.copy())

                filled_results[function] = series

            elif function == "owasp_top10":
                data = results[function]
                filled_series = []
                for serie in data:
                    result_serie = {"name": serie["name"]}
                    result_serie["value"] = {"A1": 0, "A2": 0, "A3": 0, "A4": 0, "A5": 0, "A6": 0, "A7": 0, "A8" : 0, "A9": 0, "A10": 0}
                    for row in serie["value"]:
                        result = re.sub(r'[[\]"\\]', "", row["name"]).split(",")
                        for key in result:
                            result_serie["value"][key] += row["value"]

                    filled_series.append(result_serie)

                filled_results[function] = filled_series

            elif function == "blocked_requests":
                data = results[function]
                series = {}
                # BUG: EMPTY REPORTS (Bug probably due to the  Python2 to 3 migration)
                # In mongo db, len is not valid?!?  as the line is not really needed, we can just skip it!
                # Autor: Bonomani
                #if len(data) > 0:
                series = {"SQLI": 0, "XSS": 0, "CSRF": 0, "Evade": 0, "Traversal": 0, "RFI" : 0, "LFI": 0, "RCE": 0, "PHPI": 0, "HTTP": 0, "SESS": 0}
                    for row in data:
                        result = re.findall(r'\b(\w+)\b\=(?:\b(\w+)\b)?', row["name"])
                        for tuple_key in result:
                            try:
                                series[tuple_key[0]] += (row["value"] * int(tuple_key[1]))
                            except:
                                pass

                filled_results[function] = series
                filled_results["security_radar"] = series

            elif function == "UA_based":
                data = results[function]
                series_browser, series_Os = {}, {}
                try:
                    from ua_parser import user_agent_parser

                    for row in data:
                        parsed_UA = user_agent_parser.Parse(row["name"])
                        try:
                            series_browser[parsed_UA['user_agent']['family']] += row["value"]
                        except:
                            series_browser[parsed_UA['user_agent']['family']] = row["value"]

                        try:
                            series_Os[parsed_UA['os']['family']] += row["value"]
                        except:
                            series_Os[parsed_UA['os']['family']] = row["value"]

                except ImportError:
                    series_browser = series_Os = "Import not found: UA Agent Parser"

                filled_results["browser_UA"] = series_browser
                filled_results["os_UA"] = series_Os
                filled_results.pop("UA_based", None)

            elif function == "reputation_tags":
                data = {}
                for row in results[function]:
                    tags = [ t for t in row["name"].split(",") if not t == '-' ]
                    for tag in tags:
                        if tag not in data.keys():
                            data[tag] = {}
                            data[tag]["ips"] = row["ips"]
                            data[tag]["value"] = row["value"]
                        else:
                            data[tag]["value"] += row["value"]
                            merged_ip_list = data[tag]["ips"] + row["ips"]
                            seen, ip_list = set(), []
                            for ip in merged_ip_list:
                                t = tuple(ip.items())
                                if t not in seen:
                                    seen.add(t)
                                    ip_list.append(ip)
                            data[tag]["ips"] = ip_list

                        data[tag]["ips"] = data[tag]["ips"][:20]
                        data[tag]["ips"].sort(key=lambda x:x["value"], reverse=True)
                filled_results[function] = data
            # BUG: EMPTY REPORTS (Bug probably due to the  Python2 to 3 migration)
            # TESTED WITH MONGODB ONLY, POSSIBLE IMPACT ON ELK
            # The result (CommandCursor) is lazy object that need to be iterated to have its content fill up
            # Autor: Bonomani
            else:                    
                data = [] 
                for d in results[function]:
                    data.append(d)
                filled_results[function]=data
        return filled_results
