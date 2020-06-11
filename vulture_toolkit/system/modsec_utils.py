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

import lxml

logger = logging.getLogger('debug')

def display_stats (vuln_count, num_rules_generated, num_not_supported, num_bad_urls):
    """
    :return: String with statistics
    """
    log_info = "Number of Vulnerabilities Processed: <b>" + str(vuln_count) + '</b><br/>'
    log_info = log_info + "Number of ModSecurity rules generated: <b>" + str (num_rules_generated) + '</b><br/>'
    log_info = log_info + "Number of Unsupported vulns skipped: <b>" + str (num_not_supported) + '</b><br/>'
    log_info = log_info + "Number of bad URLs (rules not gen): <b>" +str (num_bad_urls) + '</b>'
    log_info = log_info + '<br/><br/>'
    log_info = log_info + 'You can access this rules set by clicking on <b>\'return\'</b>'
    return log_info



""" Create a ModSecurity Rule from the given vulnerability
"""
def patch_vuln (vuln_type, uri_content, vuln_param, vuln_count):

    from vulture_toolkit.system.parser_utils import xss_vuln_types, sqli_vuln_types, pt_vuln_types, rfi_vuln_types, httprs_vuln_types, header_missing_vuln_types, cookie_missing_flags, method_enabled

    id = "1" + str(vuln_count)
    rule = ""


    #Only 1 param, make it a list
    if isinstance(vuln_param, lxml.etree._Element):
        vuln_param = [vuln_param.text]
    if len(vuln_param) is 0:
        vuln_param = []
    elif isinstance(vuln_param, str):
        vuln_param = [vuln_param]

    logger.info ("VirtualPatching: Vuln_type is " + str (vuln_type))

    #Cross Site Scripting
    if re.match(xss_vuln_types(), vuln_type):
        for param in vuln_param:
            if param:
                rule = "#Fix '" + vuln_type + "' on URI " + uri_content + " [" + param + "] \n"
                rule = rule + "SecRule REQUEST_FILENAME \"" + uri_content + "\" \"chain,phase:2,t:none,block,msg:'Virtual Patch for " + vuln_type + "',id:'" + id + "'" + ",tag:'WEB_ATTACK/XSS',tag:'OWASP_TOP_10/A3',logdata:'%{matched_var_name}',severity:'2' \""
                rule = rule + '\n\t'
                rule = rule + "SecRule ARGS:" + param + " \"!(^[a-zA-z0-9\-,]+$)\" \"setvar:'tx.msg=%{rule.msg}',setvar:tx.xss_score=+%{tx.critical_anomaly_score},setvar:tx.anomaly_score=+%{tx.critical_anomaly_score}\""
                rule = rule + "\n\n"

    #SQL Injection
    elif re.match(sqli_vuln_types(), vuln_type):
        for param in vuln_param:
            if param:
                rule = "#Fix '" + vuln_type + "' on URI " + uri_content + " [" + param + "] \n"
                rule = rule + "SecRule REQUEST_FILENAME \"" + uri_content + "\" \"chain,phase:2,t:none,block,msg:'Virtual Patch for " + vuln_type + "',id:'" + id + "'" + ",tag:'WEB_ATTACK/SQL_INJECTION',tag:'OWASP_TOP_10/A1',logdata:'%{matched_var_name}',severity:'2'\""
                rule = rule + '\n\t'
                rule = rule + "SecRule ARGS:" + param + " \"!(^[a-zA-z0-9\-,]+$)\" \"setvar:'tx.msg=%{rule.msg}',setvar:tx.sql_injection_score=+%{tx.critical_anomaly_score},setvar:tx.anomaly_score=+%{tx.critical_anomaly_score}\""
                rule = rule + "\n\n"

    #Path Traversal
    elif re.match(pt_vuln_types(), vuln_type):
        for param in vuln_param:
            if param:
                rule = "#Fix '" + vuln_type + "' on URI " + uri_content + " [" + param + "] \n"
                rule = rule + "SecRule REQUEST_FILENAME \"" + uri_content + "\" \"chain,phase:2,t:none,block,msg:'Virtual Patch for " + vuln_type + "',id:'" + id + "'" + ",tag:'WEB_ATTACK/LFI',logdata:'%{matched_var_name}',severity:'2'\""
                rule = rule + '\n\t'
                rule = rule + "SecRule ARGS:" + param + " \"!(^[a-zA-z0-9\-,]+$)\" \"setvar:'tx.msg=%{rule.msg}',setvar:tx.anomaly_score=+%{tx.critical_anomaly_score}\""
                rule = rule + "\n\n"

    #Remote File Inclusion
    elif re.match(rfi_vuln_types(), vuln_type):
        for param in vuln_param:
            if param:
                rule = "#Fix '" + vuln_type + "' on URI " + uri_content + " [" + param + "] \n"
                rule = rule + "SecRule REQUEST_FILENAME \"" + uri_content + "\" \"chain,phase:2,t:none,block,msg:'Virtual Patch for " + vuln_type + "',id:'" + id + "'" + ",tag:'WEB_ATTACK/RFI',logdata:'%{matched_var_name}',severity:'2'\""
                rule = rule + '\n\t'
                rule = rule + "SecRule ARGS:" + param + " \"!(^[a-zA-z0-9\-,]+$)\" \"setvar:'tx.msg=%{rule.msg}',setvar:tx.anomaly_score=+%{tx.critical_anomaly_score}\""
                rule = rule + "\n\n"

    #HTTP Response Splitting
    elif re.match(httprs_vuln_types(), vuln_type):
        for param in vuln_param:
            if param:
                rule = "#Fix '" + vuln_type + "' on URI " + uri_content + " [" + param + "] \n"
                rule = rule + "SecRule REQUEST_FILENAME \"" + uri_content + "\" \"chain,phase:2,t:none,block,msg:'Virtual Patch for " + vuln_type + "',id:'" + id + "'" + ",tag:'WEB_ATTACK/RESPONSE_SPLITTING',logdata:'%{matched_var_name}',severity:'2'\""
                rule = rule + '\n\t'
                rule = rule + "SecRule ARGS:" + param + " \"!(^[a-zA-z0-9\-,]+$)\" \"setvar:'tx.msg=%{rule.msg}',setvar:tx.anomaly_score=+%{tx.critical_anomaly_score}\""
                rule = rule + "\n\n"

    #Security HEADER Missing
    elif re.match(header_missing_vuln_types(), vuln_type):
        rule = "\t#Fix '" + vuln_type + "' \n"
        if re.match (".*X-Content-Type-Options.*", vuln_type):
            rule = rule + "\tHeader always append X-Content-Type-Options nosniff #HdrFix\n"

        elif re.match (".*X-Frame-Options.*|.*Framable Page.*", vuln_type):
            rule = rule + "\tHeader always append X-Frame-Options SAMEORIGIN #HdrFix\n"

    #Cookie missing flags
    elif re.match(cookie_missing_flags(), vuln_type):
        rule = "\t#Fix '" + vuln_type + "' \n"
        if re.match (".*HTTPOnly.*", vuln_type, re.I):
            rule = rule + "\tHeader edit Set-Cookie \"(?i)^((j?sessionid|(php)?sessid|(asp|jserv|jw)?session[-_]?(id)?|cf(id|token)|sid)=(?:(?!httponly).)+)$\" \"$1; httpOnly\" #HdrFix\n"
        elif re.match (".*secure.*", vuln_type, re.I):
            rule = rule + "\tHeader edit Set-Cookie \"(?i)^((j?sessionid|(php)?sessid|(asp|jserv|jw)?session[-_]?(id)?|cf(id|token)|sid)=(?:(?!httponly).)+)$\" \"$1; secure\" #HdrFix\n"

    #Method enabled
    elif re.match(method_enabled(), vuln_type):
        rule = "\t#Fix '" + vuln_type + "' \n"
        rule = rule + "RewriteEngine On\nRewriteCond %{REQUEST_METHOD} ^(TRACE|OPTIONS)\nRewriteRule .* – [F]\n\n"

    else:
        logger.info ("VirtualPatching: Unable to create rule for type " + str (rule))

    logger.info ("VirtualPatching: rule is " + str (rule))
    return rule
