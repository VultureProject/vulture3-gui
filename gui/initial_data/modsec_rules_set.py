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
__author__ = "Baptiste de Magnienville"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Initial data of ModSecRulesSet & ModSecRules'

import datetime

from gui.models.modsec_settings import ModSecRulesSet, ModSecRules


class Import(object):

    def process(self):
        try:
            modsec_rules_set = ModSecRulesSet.objects.get(name='Vulture RS')
        except ModSecRulesSet.DoesNotExist as e:
            modsec_rules_set = ModSecRulesSet(name='Vulture RS', type_rule='vulture')
            modsec_rules_set.save()

        date_rule = datetime.datetime.strptime('2017-03-13T08:45:00', "%Y-%m-%dT%H:%M:%S")
        
        name = "vulture_000_session.conf"
        modsec_rule = ModSecRules.objects.filter(name=name, rs=modsec_rules_set).first()
        if not modsec_rule:
            modsec_rule = ModSecRules(name=name, rs=modsec_rules_set, is_enabled=True, date_rule=date_rule)

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

        name = "vulture_001_csrf.conf"
        modsec_rule = ModSecRules.objects.filter(name=name, rs=modsec_rules_set).first()
        if not modsec_rule:
            modsec_rule = ModSecRules(name=name, rs=modsec_rules_set, is_enabled=True, date_rule=date_rule)
        modsec_rule.rule_content = """# Init collection with key based on IP+UA
SecAction "id:'1200', phase:2, t:none,nolog, initcol:col_csrf=%{remote_addr}_%{tx.ua_md5}"

# On every POST checking if the CSRF token has been informed
SecRule REQUEST_METHOD "@streq POST" "id:1201,phase:2,chain,block,log,msg:'POST request missing the CSRF token.',tag:'csrf_protection'"
SecRule &ARGS:CSRF_TOKEN "!@eq 1" "setvar:tx.inbound_anomaly_score=+%{tx.csrf_hijacking_anomaly_score}"

# On every POST checking if the CSRF token matches the random generated one
SecRule REQUEST_METHOD "@streq POST" "id:1202,phase:2,chain,capture,block,log,msg:'Invalid CSRF token. Expected %{col_csrf.token} but received %{ARGS.csrf_token}',tag:'csrf_protection'"
SecRule ARGS:CSRF_TOKEN "!@streq %{col_csrf.token}" "setvar:tx.inbound_anomaly_score=+%{tx.csrf_hijacking_anomaly_score}"

# Generate UUID for CSRF token to be injected
SecRule UNIQUE_ID "(.*)"  "id:1203,phase:2,chain,t:none,pass,nolog,t:md5,t:hexEncode,setvar:tx.uuid=%{matched_var}"
# Save UUID as CRSF token in DB for future check
SecAction "setvar:col_csrf.token=%{tx.uuid}"
# Inject the UUID as CSRF token
SecRule STREAM_OUTPUT_BODY '@rsub s/<\/form>/<input type="hidden" name="csrf_token" value="%{tx.uuid}"><\/form>/' "id:1204,phase:4,t:none,pass,nolog"
SecRule STREAM_OUTPUT_BODY "@contains </form>" "id:1205,phase:4,t:none,pass,nolog,setenv:CSRF_INJECTED=1"
# Disable cache to prevent crsf token caching
Header set Cache-Control "max-age=0, no-cache, no-store, must-revalidate" env=CSRF_INJECTED
"""
        modsec_rule.save()

        name="vulture_002_useragent.conf"
        modsec_rule = ModSecRules.objects.filter(name=name, rs=modsec_rules_set).first()
        if not modsec_rule:
            modsec_rule = ModSecRules(name=name, rs=modsec_rules_set, is_enabled=False, date_rule=date_rule)
        modsec_rule.rule_content = """# Init collection with key based on IP+UA
SecAction "id:'1300', phase:2, t:none,nolog, initcol:col_ua=%{tx.ua_md5}"

# Capture UA
SecRule REQUEST_HEADERS:User-Agent "^(.*)$" "id:'1301',phase:2,t:none,setvar:tx.ua=%{matched_var},nolog,pass"

# If Unknown UA
SecRule &COL_UA:UA "@eq 0" "id:'1302',phase:2,block,log,msg:'Unknown UA:%{tx.ua}, hash:%{tx.ua_hash}, rep:%{ENV.REPUTATION}',tag:'UA_suspicious',setvar:tx.inbound_anomaly_score=+%{tx.ua_unknown_anomaly_score},setenv:UA_UNKNOWN=1"

# If UA Anonymous
SecRule COL_UA:UA "@contains ua-anonymous" "id:'1303',phase:2,block,log,msg:'Detected UA: %{col_ua.ua}',setvar:tx.inbound_anomaly_score=+%{tx.ua_anonymous_anomaly_score},setenv:UA=ANONYMOUS"

# If UA Bot
SecRule COL_UA:UA "@contains ua-bot" "id:'1304',phase:2,block,log,msg:'Detected UA: %{col_ua.ua}',setvar:tx.inbound_anomaly_score=+%{tx.ua_bot_anomaly_score},setenv:UA=BOT"

# If UA Browser
SecRule COL_UA:UA "@contains ua-browser" "id:'1305',phase:2,block,log,msg:'Detected UA: %{col_ua.ua}',setvar:tx.inbound_anomaly_score=+%{tx.ua_browser_anomaly_score},setenv:UA=BROWSER"

# If UA Cloud
SecRule COL_UA:UA "@contains ua-cloud" "id:'1306',phase:2,block,log,msg:'Detected UA: %{col_ua.ua}',setvar:tx.inbound_anomaly_score=+%{tx.ua_cloud_anomaly_score},setenv:UA=CLOUD"

# If UA Console
SecRule COL_UA:UA "@contains ua-console" "id:'1307',phase:2,block,log,msg:'Detected UA: %{col_ua.ua}',setvar:tx.inbound_anomaly_score=+%{tx.ua_console_anomaly_score},setenv:UA=CONSOLE"

# If UA Crawler
SecRule COL_UA:UA "@contains ua-crawler" "id:'1308',phase:2,block,log,msg:'Detected UA: %{col_ua.ua}',setvar:tx.inbound_anomaly_score=+%{tx.ua_crawler_anomaly_score},setenv:UA=CRAWLER"

# If UA Emailclient
SecRule COL_UA:UA "@contains ua-emailclient" "id:'1309',phase:2,block,log,msg:'Detected UA: %{col_ua.ua}',setvar:tx.inbound_anomaly_score=+%{tx.ua_emailclient_anomaly_score},setenv:UA=EMAILCLIENT"

# If UA Emailharvester
SecRule COL_UA:UA "@contains ua-emailharvester" "id:'1310',phase:2,block,log,msg:'Detected UA: %{col_ua.ua}',setvar:tx.inbound_anomaly_score=+%{tx.ua_emailharvester_anomaly_score},setenv:UA=EMAILHARVESTER"

# If UA Mobile
SecRule COL_UA:UA "@contains ua-mobile" "id:'1311',phase:2,block,log,msg:'Detected UA: %{col_ua.ua}',setvar:tx.inbound_anomaly_score=+%{tx.ua_mobile_anomaly_score},setenv:UA=MOBILE"

# IF UA Script
SecRule COL_UA:UA "@contains ua-script" "id:'1312',phase:2,block,log,msg:'Detected UA: %{col_ua.ua}',setvar:tx.inbound_anomaly_score=+%{tx.ua_script_anomaly_score},setenv:UA=SCRIPT"
            """
        modsec_rule.save()

        name = "vulture_003_contenttype.conf"
        modsec_rule = ModSecRules.objects.filter(name=name, rs=modsec_rules_set).first()
        if not modsec_rule:
            modsec_rule = ModSecRules(name=name, rs=modsec_rules_set, is_enabled=True, date_rule=date_rule)
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
   id:1400,\
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

        name = "vulture_004_protocol.conf"
        modsec_rule = ModSecRules.objects.filter(name=name, rs=modsec_rules_set).first()
        if not modsec_rule:
            modsec_rule = ModSecRules(name=name, rs=modsec_rules_set, is_enabled=True, date_rule=date_rule)
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
   id:1401,\
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

        name = "vulture_005_fileext.conf"
        modsec_rule = ModSecRules.objects.filter(name=name, rs=modsec_rules_set).first()
        if not modsec_rule:
            modsec_rule = ModSecRules(name=name, rs=modsec_rules_set, is_enabled=True, date_rule=date_rule)
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
   id:1402,\
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

        name = "vulture_006_headers.conf"
        modsec_rule = ModSecRules.objects.filter(name=name, rs=modsec_rules_set).first()
        if not modsec_rule:
            modsec_rule = ModSecRules(name=name, rs=modsec_rules_set, is_enabled=True, date_rule=date_rule)
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
   id:1403,\
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

        conf = modsec_rules_set.get_conf()
        modsec_rules_set.conf = conf
        modsec_rules_set.save()
        
        print("Vulture RS successfully imported")