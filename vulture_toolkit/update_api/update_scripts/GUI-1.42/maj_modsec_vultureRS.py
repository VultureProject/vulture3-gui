#!/home/vlt-gui/env/bin/python2.7
# coding:utf-8

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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = """This migration script update the default ModSec Vulture Rules Set"""

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django

django.setup()

from gui.models.modsec_settings import ModSecRulesSet, ModSecRules
import datetime

if __name__ == '__main__':
    try:
        modsec_rules_set = ModSecRulesSet.objects.get(name='Vulture RS', type_rule='vulture')
    except ModSecRulesSet.DoesNotExist as e:

        """ Warning: Escpa"""

        modsec_rules_set = ModSecRulesSet(name='Vulture RS', type_rule='vulture')
        modsec_rules_set.save()

    try:
        modsec_rule = ModSecRules.objects.get(name="vulture_000_session.conf", rs=modsec_rules_set)
    except ModSecRules.DoesNotExist as e:

        modsec_rule = ModSecRules(name="vulture_000_session.conf", rs=modsec_rules_set, is_enabled=True,
                                  date_rule=datetime.datetime.strptime('2017-03-21T08:45:00', "%Y-%m-%dT%H:%M:%S"))

        modsec_rule.date_rule = datetime.datetime.strptime('2017-03-21T08:45:00', "%Y-%m-%dT%H:%M:%S")
        modsec_rule.rule_content = """# Capture UA and compute md5 sum
SecRule REQUEST_HEADERS:User-Agent "^(.*)$" "id:'999',phase:2,t:none,t:md5,t:hexEncode,setvar:tx.ua_md5=%{matched_var},nolog,pass"

# Init collection with key based on IP+UA
SecAction "id:'1000', phase:2, t:none,nolog, initcol:col_session=%{remote_addr}_%{tx.ua_md5}"

# Session cookie sent. No stored session
SecRule &REQUEST_COOKIES:JSESSIONID "@eq 1" "id:'1001',phase:2,chain,block,log,msg:'No previous session found',tag:'session_hijacking'"
SecRule &COL_SESSION:SID "@eq 0" "setvar:tx.inbound_anomaly_score=+%{tx.session_hijacking_anomaly_score},setenv:SESSION_FORCE_EXPIRE=1,setenv:SESSION_ID=%{tx.sid},setenv:SESSION_HIJACKING=1"

# Session cookie sent. Different stored session
SecRule REQUEST_COOKIES:JSESSIONID "!@streq %{col_session.sid}" "id:'1002',block,log,msg:'%{REQUEST_COOKIES.JSESSIONID} does not match %{col_session.sid}',tag:'session_hijacking',setvar:tx.inbound_anomaly_score=+%{tx.session_hijacking_anomaly_score},setenv:SESSION_HIJACKING=1"

# More than one session cookie sent
SecRule &REQUEST_COOKIES:JSESSIONID "@gt 1" "id:1003,phase:2,block,log,msg:'Too many sessions provided', tag:'session_hijacking',setvar:tx.inbound_anomaly_score=+%{tx.session_hijacking_anomaly_score},setenv:SESSION_FORCE_EXPIRE=1,setenv:SESSION_ID=%{tx.sid},setenv:SESSION_HIJACKING=1"

# Expire the cookie if needed
Header set Set-Cookie "JSESSIONID=DUMMY; expires=Thu, 01 Jan 1970 00:00:00 GMT" env=SESSION_FORCE_EXPIRE


# Initializes the session when we receive a session cookie from the server
SecRule RESPONSE_HEADERS:/Set-Cookie?/ "^(?i:JSESSIONID)=(.*?);" "id:1004,phase:3,t:none,pass,nolog,capture,setvar:col_session.sid=%{tx.1},msg:'New sid: %{tx.1}'"
"""
        modsec_rule.save()

    try:
        modsec_rule = ModSecRules.objects.get(name="vulture_003_contenttype.conf", rs=modsec_rules_set)
    except ModSecRules.DoesNotExist as e:
        modsec_rule = ModSecRules(name="vulture_003_contenttype.conf", rs=modsec_rules_set, is_enabled=True,
                                  date_rule=datetime.datetime.strptime('2017-03-13T08:45:00', "%Y-%m-%dT%H:%M:%S"))
        modsec_rule.rule_content = """# Restrict which content-types we accept.
SecRule REQUEST_METHOD "!^(?:GET|HEAD|PROPFIND|OPTIONS)$" \
  "phase:request,\
   chain,\
   t:none,\
   block,\
   msg:'Request content type is not allowed by policy',\
   rev:'2',\
   ver:'OWASP_CRS/3.0.0',\
   maturity:'9',\
   accuracy:'9',\
   id:920420,\
   severity:'CRITICAL',\
   logdata:'%{matched_var}',\
   tag:'application-multi',\
   tag:'language-multi',\
   tag:'platform-multi',\
   tag:'attack-protocol',\
   tag:'OWASP_CRS/POLICY/ENCODING_NOT_ALLOWED',\
   tag:'WASCTC/WASC-20',\
   tag:'OWASP_TOP_10/A1',\
   tag:'OWASP_AppSensor/EE2',\
   tag:'PCI/12.1'"
SecRule REQUEST_HEADERS:Content-Type "^([^;\s]+)" \
       "chain,\
        capture"
SecRule TX:0 "!^%{tx.allowed_request_content_type}$" \
            "t:none,\
             ctl:forceRequestBodyVariable=On,\
             setvar:'tx.msg=%{rule.msg}',\
             setvar:tx.anomaly_score=+%{tx.critical_anomaly_score},\
             setvar:tx.%{rule.id}-OWASP_CRS/POLICY/CONTENT_TYPE_NOT_ALLOWED-%{matched_var_name}=%{matched_var}"
            """
        modsec_rule.save()

    try:
        modsec_rule = ModSecRules.objects.get(name="vulture_004_protocol.conf", rs=modsec_rules_set)
    except ModSecRules.DoesNotExist as e:
        modsec_rule = ModSecRules(name="vulture_004_protocol.conf", rs=modsec_rules_set, is_enabled=True,
                                  date_rule=datetime.datetime.strptime('2017-03-13T08:45:00', "%Y-%m-%dT%H:%M:%S"))
        modsec_rule.rule_content = """# Restrict protocol versions.
SecRule REQUEST_PROTOCOL "!@within %{tx.allowed_http_versions}" \
  "phase:request,\
   t:none,\
   block,\
   msg:'HTTP protocol version is not allowed by policy',\
   severity:'CRITICAL',\
   rev:'2',\
   ver:'OWASP_CRS/3.0.0',\
   maturity:'9',\
   accuracy:'9',\
   id:920430,\
   tag:'application-multi',\
   tag:'language-multi',\
   tag:'platform-multi',\
   tag:'attack-protocol',\
   tag:'OWASP_CRS/POLICY/PROTOCOL_NOT_ALLOWED',\
   tag:'WASCTC/WASC-21',\
   tag:'OWASP_TOP_10/A6',\
   tag:'PCI/6.5.10',\
   logdata:'%{matched_var}',\
   setvar:'tx.msg=%{rule.msg}',\
   setvar:tx.anomaly_score=+%{tx.critical_anomaly_score},\
            """
        modsec_rule.save()

    try:
        modsec_rule = ModSecRules.objects.get(name="vulture_005_fileext.conf", rs=modsec_rules_set)
    except ModSecRules.DoesNotExist as e:
        modsec_rule = ModSecRules(name="vulture_005_fileext.conf", rs=modsec_rules_set, is_enabled=True,
                                  date_rule=datetime.datetime.strptime('2017-03-13T08:45:00', "%Y-%m-%dT%H:%M:%S"))
        modsec_rule.rule_content = """# Restrict file extension
SecRule REQUEST_BASENAME "\.(.*)$" \
  "chain,\
   capture,\
   phase:request,\
   t:none,t:urlDecodeUni,t:lowercase,\
   block,\
   msg:'URL file extension is restricted by policy',\
   severity:'CRITICAL',\
   rev:'2',\
   ver:'OWASP_CRS/3.0.0',\
   maturity:'9',\
   accuracy:'9',\
   id:920440,\
   logdata:'%{TX.0}',\
   tag:'application-multi',\
   tag:'language-multi',\
   tag:'platform-multi',\
   tag:'attack-protocol',\
   tag:'OWASP_CRS/POLICY/EXT_RESTRICTED',\
   tag:'WASCTC/WASC-15',\
   tag:'OWASP_TOP_10/A7',\
   tag:'PCI/6.5.10',logdata:'%{TX.0}',\
   setvar:tx.extension=.%{tx.1}/"
SecRule TX:EXTENSION "@within %{tx.restricted_extensions}" \
       "t:none,\
        setvar:'tx.msg=%{rule.msg}',\
        setvar:tx.anomaly_score=+%{tx.critical_anomaly_score},\
        setvar:tx.%{rule.id}-OWASP_CRS/POLICY/EXT_RESTRICTED-%{matched_var_name}=%{matched_var}"
            """
        modsec_rule.save()

    try:
        modsec_rule = ModSecRules.objects.get(name="vulture_006_headers.conf", rs=modsec_rules_set)
    except ModSecRules.DoesNotExist as e:
        modsec_rule = ModSecRules(name="vulture_006_headers.conf", rs=modsec_rules_set, is_enabled=True,
                                  date_rule=datetime.datetime.strptime('2017-03-13T08:45:00', "%Y-%m-%dT%H:%M:%S"))
        modsec_rule.rule_content = """# Restricted HTTP headers
SecRule REQUEST_HEADERS_NAMES "@rx ^(.*)$" \
  "msg:'HTTP header is restricted by policy (%{MATCHED_VAR})',\
   severity:'CRITICAL',\
   phase:request,\
   t:none,\
   block,\
   rev:'2',\
   ver:'OWASP_CRS/3.0.0',\
   maturity:'9',\
   accuracy:'9',\
   id:920450,\
   capture,\
   logdata:' Restricted header detected: %{matched_var}',\
   tag:'application-multi',\
   tag:'language-multi',\
   tag:'platform-multi',\
   tag:'attack-protocol',\
   tag:'OWASP_CRS/POLICY/HEADER_RESTRICTED',\
   tag:'WASCTC/WASC-21',\
   tag:'OWASP_TOP_10/A7',\
   tag:'PCI/12.1',\
   tag:'WASCTC/WASC-15',\
   tag:'OWASP_TOP_10/A7',\
   tag:'PCI/12.1',\
   t:lowercase,\
   setvar:'tx.header_name_%{tx.0}=/%{tx.0}/',\
   chain"
SecRule TX:/^HEADER_NAME_/ "@within %{tx.restricted_headers}" \
   	"setvar:'tx.msg=%{rule.msg}',\
   	 setvar:tx.anomaly_score=+%{tx.critical_anomaly_score},\
   	 setvar:'tx.%{rule.id}-OWASP_CRS/POLICY/HEADERS_RESTRICTED-%{matched_var_name}=%{matched_var}'"
            """
        modsec_rule.save()

    print "Vulture RS successfully updated"
