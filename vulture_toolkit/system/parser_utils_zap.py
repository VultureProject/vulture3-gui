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


def zap_parser (vuln_types, xml_document):

    """ Build a ModSecurity Rules Set from vulnerabilities found in XML buffer

    :param vuln_types: The list of vulnerabilities that we can support
    :param xml_document: XML scan result
    :returns: a list with [string buffer containing ModSecurity rules, log output]
    """

    # Open the XML Document
    try:
        root = etree.fromstring(xml_document)
    except etree.LxmlError as e:
        logger.exception(e)
        return None

    virtual_policy_list={}

    app_list    = root.xpath('/OWASPZAPReport//site')

    for app in app_list:
        app_name = app.get("name")

        num_rules_generated = 0
        num_not_supported = 0
        num_bad_urls = 0
        vuln_count = 0
        rule_buffer = ""
        header_rule_buffer = []

        # Getting all the "instance" tags which <uri> and <param> tags are into
        alert_list  = root.xpath('/OWASPZAPReport/site[@name="'+str(app_name)+'"]/alerts//alertitem')

        for type in alert_list:
            vuln_type = type.find('alert').text

            match=None
            for expr in vuln_types:
                if re.match (expr, vuln_type):
                    match=1
                    break

            if match is None:
                logger.info("ZAP Parser: " + vuln_type + "' is not supported yet")
                num_not_supported = num_not_supported + 1
                vuln_count = vuln_count + 1
                continue

            #Ok, we have one or multiple vulnerabilities that we should be able to fix
            # First, we get <instance> tags inside <vuln> current tag
            vuln_instances = []
            try:
                vuln_instances = type.findall('instances/instance')
            except Exception as e:
                pass

            for instance in vuln_instances:
                # Getting <uri> (and <param> tag) inside that <instance> tag
                vuln_uri = instance.find('uri').text
                vuln_param = ""
                try:
                    vuln_param = instance.find('param').text
                except Exception as e:
                    pass

                logger.info("ZAP Parser: Going to handle vuln type " + str (vuln_type))
                logger.info("ZAP Parser: URI List =  " + str (vuln_uri))
                logger.info("ZAP Parser: Param =  " + str (vuln_param))

                #Check if the URI is valid
                if check_uri (vuln_uri):
                    #Get the URI content (remove the host and the query string)
                    uri_content = get_uri_content(vuln_uri)

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
                    logger.info("ZAP Parser: Invalid URI " + str (vuln_uri))
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
