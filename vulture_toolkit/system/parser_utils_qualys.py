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
__author__ = "Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'System Utils Toolkit'

import logging
import re

from lxml import etree

from vulture_toolkit.system.http_utils import check_uri, get_uri_content, get_uri_fqdn_path
from vulture_toolkit.system.modsec_utils import patch_vuln, display_stats

logger = logging.getLogger('debug')


def qualys_parser (vuln_types, xml_document):

    """ Build a ModSecurity Rules Set from vulnerabilities found in XML buffer

    :param vuln_types: The list of vulnerabilities that we can support
    :param xml_document: XML scan result
    :returns: a list with [string buffer containing ModSecurity rules, log output]
    """

    #Open the XML Document
    try:
        root = etree.fromstring(xml_document)
    except etree.LxmlError as e:
        return None

    virtual_policy_list={}

    #Initialize counters
    num_rules_generated = {}
    num_not_supported = {}
    num_bad_urls = {}
    vuln_count = {}
    rule_buffer = {}
    header_rule_buffer = {}

    #First, build the list of QID inside the report
    #This is need to classify vulnerabilities
    qid_list = root.xpath('/WAS_SCAN_REPORT/GLOSSARY/QID_LIST//QID')
    qid_dict = {}
    param_dict = {}

    for qid in qid_list:
        id=None
        type=None
        for c in qid:
            if c.tag == "QID":
                id = c.text

            if id and c.tag == "TITLE":
                type = c.text

            if id and type:
                qid_dict[id] = type
                break

    vuln_list    = root.xpath('/WAS_SCAN_REPORT/RESULTS//VULNERABILITY_LIST//VULNERABILITY')


    for vuln in vuln_list:
        qid=""
        id=""
        vuln_uri=""
        vuln_param=""

        for c in vuln:
            if c.tag == "QID":
                qid = c.text
            elif c.tag == "ID":
                id = c.text
            elif c.tag == "URL":
                vuln_uri = c.text
            elif c.tag == "PARAM":
                vuln_param = c

        vuln_type = qid_dict[qid]

        match=None
        for expr in vuln_types:
            if re.match (expr, vuln_type):
                match=1
                break

        logger.info("Qualys Parser: Going to handle vuln type " + str (vuln_type))
        logger.info("Qualys Parser: URI List =  " + str (vuln_uri))

        #Check if the URI is valid
        if check_uri (vuln_uri):
            #Get the FQDN
            app_name = get_uri_fqdn_path(vuln_uri)
            logger.info("Qualys Parser: App Name =  " + str (app_name))

            init=False
            try:
                b = vuln_count[app_name]
            except KeyError as e:
                init=True
                pass

            if init:
                vuln_count[app_name] = 0
                num_not_supported[app_name] = 0
                num_rules_generated[app_name] = 0
                num_bad_urls[app_name] = 0
                header_rule_buffer[app_name] = []
                rule_buffer[app_name]=""

        else:
            logger.info("Qualys Parser: Invalid URI " + str (vuln_uri))
            num_bad_urls[app_name] = num_bad_urls[app_name] + 1
            app_name="INVALID_URI"
            vuln_count[app_name] = vuln_count[app_name] + 1
            continue

        if match is None:
            logger.info("Qualys Parser: " + vuln_type + "' is not supported yet")
            num_not_supported[app_name] = num_not_supported[app_name] + 1
            vuln_count[app_name] = vuln_count[app_name] + 1
            continue

        #Ok, we have a vulnerability that we should be able to fix
        #Check if the URI is valid
        if check_uri (vuln_uri):
            #Get the URI content (remove the host and the query string)
            uri_content = get_uri_content(vuln_uri)
            #Get the FQDN
            app_name = get_uri_fqdn_path (vuln_uri)

            #Let's protect our application
            rule = patch_vuln (vuln_type, uri_content, vuln_param, vuln_count[app_name])

            #Handle special case of header rules: must be unique
            if re.search(".*#HdrFix.*",rule):
                rule = re.sub ("#HdrFix","",rule)
                if rule not in header_rule_buffer[app_name]:
                    header_rule_buffer[app_name].append (rule)
            elif rule:
                rule_buffer[app_name] = rule_buffer[app_name] + rule + "\n"
            num_rules_generated[app_name] = num_rules_generated[app_name] + 1

            vuln_count[app_name] = vuln_count[app_name] + 1


    #Job's done - Add Header rule buffer, if not empty
    for app_name, nb in vuln_count.items():
        if header_rule_buffer.get(app_name):
            tmp = "<IfModule headers_module>\n"
            for header in header_rule_buffer[app_name]:
                tmp = tmp + header
            tmp = tmp + "</IfModule>\n\n"

            try:
                rb = rule_buffer[app_name]
            except KeyError as e:
                rule_buffer[app_name]=""
                pass

            rule_buffer[app_name] = tmp + rule_buffer[app_name]


        log_info = display_stats (vuln_count[app_name], num_rules_generated[app_name], num_not_supported[app_name], num_bad_urls[app_name])
        virtual_policy_list[app_name] = [rule_buffer[app_name], log_info]

    return virtual_policy_list
