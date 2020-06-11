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
__author__ = "Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django models dedicated to Apache mod_security'

import datetime
import logging
import os

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from mongoengine import (BooleanField, DateTimeField, Document, DynamicDocument, ListField, PULL, ReferenceField,
                         StringField)

logger = logging.getLogger('modsec')


class ModSecRulesSet(DynamicDocument):
    """ Vulture mod_security rules set model representation
    name:           A friendly name for the mod_security rules set
    is_crs:         Is the rule related to an OWASP rules. Usefull
     to threat rules as 'group of read-only rules'.
    is_trustwave:   Is the rule related to Trustwave rules.
    Usefull to threat rules as 'group of read-only rules'.
    """

    TYPE_RULES = (
        ('crs', 'OWASP CRS'),
        ('trustwave', 'TrustWave'),
        ('virtualpatching', 'Virtual Patching'),
        ('vulture', 'Vulture RS'),
        ('wlbl', 'WL/BL'),
        ('custom', 'Custom')
    )

    name = StringField(required=True,
                       help_text=_('Friendly Name to reference the rules set'))
    type_rule = StringField(choices=TYPE_RULES, required=True)

    conf = StringField(required=False)

    def __str__(self):
        return self.name

    def get_conf(self):
        """Returns mod_security configuration used in httpd.conf"""
        ret = "\n"

        for rule in ModSecRules.objects.filter(rs=self).order_by('name'):
            if rule.is_enabled and not rule.is_data:
                ret += "Include {}{}\n".format(self.rules_directory, rule.filename)
        
        return ret

    def write_conf(self):
        """Write mod_security rules on disk"""

        rules = ModSecRules.objects.filter(rs=self).order_by('name')
        path = self.rules_directory
        # Creating RuleSet directory
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except Exception as e:
                logger.error("Directory already exists: " + str(path))
                logger.exception(e)
        # Writing rule files
        for rule in rules:
            # Skipping not enabled rules
            if not rule.is_enabled:
                continue
            filename = '{}{}'.format(path, rule.filename)
            # Unlink rule file, just to be sure...
            if not rule.is_enabled and os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception as e:
                    logger.error("Unable to delete file: " + str(filename))
                    logger.exception(e)
            # Creating rule file
            try:
                f = open(filename, 'wb')
                f.write(rule.rule_content.encode('utf8', 'ignore'))
                f.close()
            except Exception as e:
                logger.error("Unable to create rule file: {}".format(filename))
                logger.exception(e)

        return True


    def need_restart(self):
        """ Method used to check if on-disk rules are equals to database rules

        :return: True if on-disk rules need to be updated with database rules,
        False otherwise
        """
        rules = ModSecRules.objects.filter(rs=self, is_enabled=True).order_by('name')
        path = self.rules_directory
        for rule in rules:
            filename = '{}{}'.format(path, rule.filename)
            logger.debug("Looking if {} rules differs from db".format(filename))
            try:
                f = open(filename, 'rb')
                disk_content = f.read()
                disk_content = disk_content.decode('utf-8', 'ignore')
                f.close()
                if disk_content != rule.rule_content:
                    logger.debug("{} differs, we need to rewrite this rule".format(filename))
                    return True
            except Exception as e:
                logger.error("Unable to check if {} rule is up to date".format(rule.name))
                logger.exception(e)
                return True
        return False

    @property
    def rules_directory(self):
        """ Directory where rules are stored

        :return:
        """
        return '{}modsec/'.format(settings.CONF_DIR)


class ModSecDOSRules(DynamicDocument):
    enable = BooleanField(required=True, default=True)

    url = StringField(required=True, default='/login.php',
                       help_text=_('Url on which the following values will be applied'))

    burst_time_slice = StringField(required=True, default='60',
                                    help_text=_('Time interval window to monitor for bursts, in seconds'))

    counter_threshold = StringField(required=True, default='100',
                                     help_text=_('Threshold to trigger a burst'))

    block_timeout = StringField(required=True, default='600',
                                 help_text=_('Temporary block timeout, in seconds'))



class ModSecSpecificRulesSet(DynamicDocument):
    """ Specific Rules Set for a public dir or an url """
    url = StringField(required=True, default='/login/',
                      help_text=_('Url or public_dir on which the Rules Set will be applied'))

    rs = ReferenceField('ModSecRulesSet', required=True, reverse_delete_rule=PULL,
                        help_text=_('The Rules Set to apply'))




class ModSecRules(DynamicDocument):
    """ Vulture mod_security rule model representation
    name:       A friendly name for the mod_security rule
    rs:             The rules set the rule belongs to
    rule_content:   The rule directives
    is_enabled:     Is the rule enabled or not ?
    """

    name = StringField(required=False,
                       help_text=_('Friendly Name to reference the rule'))
    rs = ReferenceField('ModSecRulesSet', reverse_delete_rule=PULL,
                        help_text=_('The Rules Set this rule belongs to'))
    rule_content = StringField(required=True)
    is_enabled = BooleanField(default=True)
    date_rule = DateTimeField(required=True, default=datetime.datetime.now())

    @property
    def is_data(self):
        return self.name.endswith('.data')

    @property
    def filename(self):
        if self.is_data:
            return os.path.basename(self.name)
        else:
            return '{}.rules'.format(self.id)

    def __str__(self):
        return self.rule_content


class ModSec(DynamicDocument):
    """ Vulture mod_security model representation
    name:       A friendly name for the mod_security profile
    FIXME
    """

    ON_OFF = (
        ('On', 'Yes'),
        ('Off', 'No')
    )

    AUDIT_ENGINE = (
        ('On', 'Log all transactions'),
        ('Off', 'Do not log any transactions'),
        ('RelevantOnly', 'Log only relevant transactions'),
    )

    CONN_ENGINE = (
        ('On', 'On: Process rules'),
        ('Off', 'Off: Do not process rules'),
        ('DetectionOnly', 'DetectionOnly: Process rules without disruptive actions'),
    )

    COOKIE_FORMAT = (
        ('0', 'Version 0 (Netscape) Cookie'),
        ('1', 'Version 1 Cookie'),
    )

    LOG_CONTROL = (
        ('log', 'Log alerts to both the Apache error_log and ModSecurity audit_log'),
        ('nolog,auditlog', 'Log alerts *only* to the ModSecurity audit_log'),
        ('log,noauditlog', 'Log alerts *only* to the Apache error_log file'),
    )

    name = StringField(required=True, default="Default Policy", unique=True,
                       help_text=_('Friendly Name to reference the profile'))

    secauditengine = StringField(required=True, choices=AUDIT_ENGINE, default='Off',
                                 help_text=_('Audit Engine for transaction logs'))
    secauditlogrelevantstatus = StringField(required=False,
                                            default='^(5|4(?!04))',
                                            help_text=_('Relevant status code to be logged'))
    secconnengine = StringField(required=True, default='On',
                                choices=CONN_ENGINE,
                                help_text=_('Configures the connection engine'))
    secbodyinspection = BooleanField(default=True, help_text=_("Enable body inspection"))
    seccontentinjection = BooleanField(default=True, help_text=_(
        'Enable content injection using actions "append" and "prepend"'))
    secdisablebackendcompression = BooleanField(default=True,
        help_text=_('Useful if you want to inspect backend responses'))
    secargumentseparator = StringField(required=True, default='&', help_text=_(
        'Separator for application/x-www-form-urlencoded'))
    seccollectiontimeout = StringField(required=False, default='3600',
                                       help_text=_('Specifies the collections timeout, in seconds'))
    seccookieformat = StringField(required=False, default='0',
                                  choices=COOKIE_FORMAT,
                                  help_text=_('Select the cookie format'))
    seccookiev0separator = StringField(required=False, default=';',
                                       help_text=_('Select the character to use as the separator for cookie content'))
    # Operation mode & scoring settings
    logging_control = StringField(required=True, default='nolog,auditlog',
                                  choices=LOG_CONTROL,
                                  help_text=_('Select the Alert Logging Control'))
    security_level = StringField(required=True, default="5",
                                      help_text=_('Security Level'))
    block_desktops_ua = BooleanField(default=False, help_text=_(
        'Block desktop browsers User-Agent'))
    block_crawlers_ua = BooleanField(default=False, help_text=_(
        'Block crawlers User-Agent'))
    block_suspicious_ua = BooleanField(default=False, help_text=_(
        'Block all suspicious. unknown and empty User-Agent'))
    critical_anomaly_score = StringField(required=True, default="4",
                                         help_text=_('Critical anomaly score'))
    error_anomaly_score = StringField(required=True, default="3",
                                      help_text=_('Error anomaly score'))
    warning_anomaly_score = StringField(required=True, default="2",
                                        help_text=_('Warning anomaly score'))
    notice_anomaly_score = StringField(required=True, default="1",
                                       help_text=_('Notice anomaly score'))
    ua_unknown_anomaly_score = StringField(required=False, default="2",
                                       help_text=_('UA unknown anomaly score'))
    session_hijacking_anomaly_score = StringField(required=False, default="2",
                                       help_text=_('Session hijacking anomaly score'))
    csrf_hijacking_anomaly_score = StringField(required=False, default="2",
                                       help_text=_('CSRF hijacking anomaly score'))
    ua_anonymous_anomaly_score = StringField(required=False, default="2",
                                           help_text=_('UA anonymous anomaly score'))
    ua_bot_anomaly_score = StringField(required=False, default="2",
                                           help_text=_('UA bot anomaly score'))
    ua_browser_anomaly_score = StringField(required=False, default="0",
                                           help_text=_('UA browser anomaly score'))
    ua_cloud_anomaly_score = StringField(required=False, default="2",
                                           help_text=_('UA cloud anomaly score'))
    ua_console_anomaly_score = StringField(required=False, default="2",
                                           help_text=_('UA console anomaly score'))
    ua_crawler_anomaly_score = StringField(required=False, default="0",
                                           help_text=_('UA crawler anomaly score'))
    ua_emailclient_anomaly_score = StringField(required=False, default="2",
                                           help_text=_('UA emailclient anomaly score'))
    ua_emailharvester_anomaly_score = StringField(required=False, default="2",
                                           help_text=_('UA emailharvester anomaly score'))
    ua_mobile_anomaly_score = StringField(required=False, default="0",
                                           help_text=_('UA mobile anomaly score'))
    ua_script_anomaly_score = StringField(required=False, default="2",
                                           help_text=_('UA script anomaly score'))
    # vlt_injection = StringField(required=True, default="1", help_text=_('SQL threshold'))
    # vlt_xss = StringField(required=True, default="1", help_text=_('XSS threshold'))
    # vlt_rfi = StringField(required=True, default="1", help_text=_('RFI threshold'))
    # vlt_lfi = StringField(required=True, default="1", help_text=_('LFI threshold'))
    # vlt_rce = StringField(required=True, default="1", help_text=_('RCE threshold'))
    # vlt_leak = StringField(required=True, default="1", help_text=_('Leak threshold'))
    # vlt_protocol = StringField(required=True, default="1", help_text=_('Protocol problem threshold'))
    # vlt_session = StringField(required=True, default="1", help_text=_('Session threshold'))
    # vlt_csrf = StringField(required=True, default="1", help_text=_('CSRF threshold'))
    # vlt_evade = StringField(required=True, default="1", help_text=_('Evade threshold'))
    # vlt_suspicious = StringField(required=True, default="1", help_text=_('Suspicious threshold'))
    inbound_anomaly_score_threshold = StringField(required=True, default="18",
                                              help_text=_('Inbound Score Threshold'))
    outbound_anomaly_score_threshold = StringField(required=False, default="18",
                                               help_text=_('Outbound Score Threshold'))
    # HTTP Policy Settings
    max_num_args = StringField(required=True, default="255",
                               help_text=_('Maximum number of arguments in request'))
    arg_name_length = StringField(required=True, default="100",
                                  help_text=_('Limit the argument name length'))
    arg_length = StringField(required=True, default="400",
                             help_text=_('Limit the value length'))
    total_arg_length = StringField(required=True, default="64000",
                                   help_text=_('Limit the arguments total length'))
    max_file_size = StringField(required=True, default="1048576",
                                help_text=_('Limit individual file size'))
    combined_file_sizes = StringField(required=True, default="1048576",
                                      help_text=_('Limit combined file size'))
    allowed_request_content_type = StringField(required=True,
                                               default='application/x-www-form-urlencoded,multipart/form-data,text/xml,application/xml,application/x-amf,application/json,application/json-rpc',
                                               help_text=_('Limit combined file size'))
    allowed_http_versions = StringField(required=True,
                                        default='HTTP/1.0,HTTP/1.1,HTTP/2.0',
                                        help_text=_('Limit combined file size'))
    restricted_extensions = StringField(required=True,
                                        default='.asa,.asax,.ascx,.axd,.backup,.bak,.bat,.cdx,.cer,.cfg,.cmd,.com,.config,.conf,.cs,.csproj,.csr,.dat,.db,.dbf,.dll,.dos,.htr,.htw,.ida,.idc,.idq,.inc,.ini,.key,.licx,.lnk,.log,.mdb,.old,.pass,.pdb,.pol,.printer,.pwd,.resources,.resx,.sql,.sys,.vb,.vbs,.vbproj,.vsdisco,.webinfo,.xsd,.xsx',
                                        help_text=_('Limit combined file size'))
    restricted_headers = StringField(required=True,
                                     default='Proxy-Connection,Lock-Token,Content-Range,Translate,via,if',
                                     help_text=_('Limit combined file size'))
    # DDOS Protection
    dos_enable_rule = BooleanField(default=False, required=False, help_text=_("Enable or disable this global rule"))
    dos_burst_time_slice = StringField(required=True, default='60',
                                       help_text=_('Time interval window to monitor for bursts, in seconds'))
    dos_counter_threshold = StringField(required=True, default='100',
                                        help_text=_('Threshold to trigger a burst'))
    dos_block_timeout = StringField(required=True, default='600',
                                    help_text=_('Temporary block timeout, in seconds'))

    dos_rules = ListField(ReferenceField('ModSecDOSRules', reverse_delete_rule=PULL), help_text=_("Add url's specific DOS rule"))

    # UTF8 Support
    crs_validate_utf8_encoding = BooleanField(
        help_text=_('Activate if your site uses UTF8 encoding (works only with the OWASP rules set)'))
    # XML BODY Parsing
    xml_enable = BooleanField(
        help_text=_('Initiate XML Processor in case of XML content-type (works with Mod Defender or with the OWASP rules set)'))
    # Block Invalid BODY
    reqbody_error_enable = BooleanField(help_text=_('Block Invalid BODY (works with Mod Defender or with the OWASP rules set)'))

    customconf = StringField(required=False,
                             default='#Place your custom ModSecurity directives here')
    defender_request_body_limit = StringField(required=True, default='131072',
                                       help_text=_('The maximum post body size to analyze, in bytes'))
    defender_enable = BooleanField(default=True, help_text=_("Enable Mod Defender"))
    defender_libinjection_sql_enable = BooleanField(default=True, help_text=_("Enable libinjection SQL scan"))
    defender_libinjection_xss_enable = BooleanField(default=True, help_text=_("Enable libinjection XSS scan"))


    def __str__(self):
        return self.name

    def get_attr(self, a, sep=None):
        """Returns attribute used in TAG input
        :param: the attribute to get
        :param: if sep is True, format the output for vulture_httpd.conf using the given separator
        """
        ret = ""
        for s in getattr(self, a).split(','):
            if sep:
                if a == 'restricted_extensions':
                    s += '/'
                if a == 'restricted_headers':
                    s = '/{}/'.format(s)
                ret = ret + s + sep
            else:
                ret = ret + '"' + s + '",'
        return ret[:-1]


class ModSecScan(Document):
    """ Vulture security scan result representation
    type:       The scan type
    content:    The scan content
    """

    SCAN_TYPE = (
        ('acunetix_9', 'XML - Acunetix v9'),
        ('qualys', 'XML - Qualysguard WAS'),
        ('zap', 'XML - OWASP Zed Attack Proxy'),
    )

    type = StringField(required=True, choices=SCAN_TYPE)
    file = StringField(required=True)

