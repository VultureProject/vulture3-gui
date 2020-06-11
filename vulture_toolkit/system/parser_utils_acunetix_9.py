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

from vulture_toolkit.system.http_utils import check_uri, get_uri_content
from vulture_toolkit.system.modsec_utils import patch_vuln, display_stats

logger = logging.getLogger('debug')

def acunetix_9_parser (vuln_types, xml_document):

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

    try:
        uri = root.xpath('/ScanGroup/Scan/StartURL')
        app_name = uri[0].text
    except Exception as e:
        return None

    num_rules_generated = 0
    num_not_supported = 0
    num_bad_urls = 0
    vuln_count = 0
    rule_buffer = ""
    header_rule_buffer = []

    alert_list  = root.xpath('/ScanGroup/Scan/ReportItems/ReportItem//Name')
    uri_list    = root.xpath('/ScanGroup/Scan/ReportItems/ReportItem//Affects')
    param_list  = root.xpath('/ScanGroup/Scan/ReportItems/ReportItem//Parameter')

    for type in alert_list:
        vuln_type = type.text

        match=None
        for expr in vuln_types:
            if re.match (expr, vuln_type):
                match=1
                break

        if match is None:
            logger.info("Acunetix Parser: " + vuln_type + "' is not supported yet")
            num_not_supported = num_not_supported + 1
            vuln_count = vuln_count + 1
            continue

        logger.info("Acunetix Parser: Going to handle vuln type " + str (vuln_type))
        logger.info("Acunetix Parser: App Name =  " + str (app_name))
        logger.info("Acunetix Parser: URI List =  " + str (uri_list[vuln_count].text))
        logger.info("Acunetix Parser: Param =  " + str (param_list[vuln_count]))

        #Ok, we have a vulnerability that we should be able to fix
        u = uri_list[vuln_count].text
        if u == "Web Server":
            u="/"
        vuln_uri    = re.sub ('/$','',app_name) + u
        vuln_param  = param_list[vuln_count]


        #Check if the URI is valid
        if check_uri (vuln_uri):
            #Get the URI content (remove the host and the query string)
            uri_content = get_uri_content(vuln_uri)
            logger.info("Acunetix Parser: URI Content " + str (uri_content))

            #Let's protect our application
            rule = patch_vuln (vuln_type, uri_content, vuln_param, vuln_count)

            #Handle special case of header rules: must be unique
            if re.search(".*#HdrFix.*",rule):
                rule = re.sub ("#HdrFix","",rule)
                if rule not in header_rule_buffer:
                    header_rule_buffer.append (rule)
            elif rule:
                rule_buffer = rule_buffer + rule + "\n"
                num_rules_generated = num_rules_generated + 1


        else :
            logger.info("Acunetix Parser: Invalid URI " + str (vuln_uri))
            num_bad_urls = num_bad_urls + 1

        vuln_count = vuln_count + 1

    #Job's done - Add Header rule buffer, if not empty
    if header_rule_buffer:
        num_rules_generated = num_rules_generated + 1
        tmp = "<IfModule headers_module>\n"
        for header in header_rule_buffer:
            tmp = tmp + header
        tmp = tmp + "</IfModule>\n\n"
        rule_buffer = tmp + rule_buffer

    log_info = display_stats (vuln_count, num_rules_generated, num_not_supported, num_bad_urls)
    virtual_policy_list[app_name] = [rule_buffer, log_info]

    return virtual_policy_list
