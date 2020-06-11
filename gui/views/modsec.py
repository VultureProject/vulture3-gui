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
__doc__ = 'Django views dedicated to mod_ssl profiles'

import datetime
import json
import logging
import os
import re
import tempfile
import uuid
import zipfile
import requests
from hashlib import sha1
from uuid import getnode as get_mac
from threading import Thread

from bson.objectid import ObjectId
from django.http import HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.html import escape

from gui.decorators import group_required
from gui.forms.modsec_settings import ModSecForm, ModSecScanForm, ModSecRulesSetForm
from gui.models.application_settings import Application
from gui.models.modsec_settings import ModSec, ModSecRules, ModSecRulesSet, ModSecDOSRules
from gui.models.system_settings import Cluster
from gui.signals.gui_signals import config_modified
from vulture_toolkit.log.elasticsearch_client import ElasticSearchClient
from vulture_toolkit.log.mongodb_client import MongoDBClient
from vulture_toolkit.system.parser_utils import scan_to_modsec
from vulture_toolkit.update_api.update_utils import UpdateUtils

logger = logging.getLogger('debug')

@group_required('administrator', 'security_manager')
def policy_list(request):
    """ Page dedicated to show mod_security profiles list
    """
    try:
        modsec_list = ModSec.objects()
        policy_list = [{"modsec": item, "is_delible": False} if len(Application.objects(modsec_policy=item).values_list("name")) else {"modsec": item, "is_delible": True} for item in modsec_list]
    except:
        policy_list = None

    return render_to_response('modsec.html', {'policy_list': policy_list}, context_instance=RequestContext(request))


@group_required('administrator', 'security_manager')
def rulesset_list(request, type_modsec):
    """ Page dedicated to show mod_security rules set list
    """

    try:
        if (type_modsec == 'virtualpatching'):
            rulesset_list = ModSecRulesSet.objects(type_rule=type_modsec)
        else:
            rulesset_list = []
            for modsecrules_set in ModSecRulesSet.objects():
                if modsecrules_set.type_rule == 'wlbl':
                    if len(ModSecRules.objects.filter(rs=modsecrules_set)):
                        rulesset_list.append(modsecrules_set)
                else:
                    rulesset_list.append(modsecrules_set)
    except:
        rulesset_list = None

    cluster         = Cluster.objects.get()
    system_settings = cluster.system_settings
    global_conf     = system_settings.global_settings

    if global_conf.trustwave_url and global_conf.trustwave_user:
        trustwave_enable=1
    else:
        trustwave_enable=None

    return render_to_response('modsec_rulesset.html', {'rulesset_list': rulesset_list, 'trustwave_enable':trustwave_enable, 'type_modsec': type_modsec}, context_instance=RequestContext(request))


@group_required('administrator', 'security_manager')
def clone(request, object_id=None):

    """ View dedicated to mod_security policy cloning
    :param object_id: MongoDB object_id of mod_security profile
    :param request: Django request object
    """

    modsec = ModSec.objects.with_id(ObjectId(object_id))
    modsec.pk = None
    modsec.name = 'Copy of ' + str(modsec.name)
    modsec.save()
    return HttpResponseRedirect('/firewall/modsec/')


@group_required('administrator', 'security_manager')
def edit(request, object_id=None):

    """ View dedicated to mod_security policy management

    :param object_id: MongoDB object_id of mod_security profile
    :param request: Django request object
    """

    modsec = None
    dos_rules = []
    # Retrieving access configuration
    if object_id:
        modsec = ModSec.objects.with_id(ObjectId(object_id))

    if request.method == 'POST':
        form = ModSecForm(request.POST, instance=modsec)
        dataPosted = request.POST
        dataPostedRaw = str(request.body).split("&")
        for data in dataPosted:
            m = re.match('DOSRule_url_(\d+)', data)
            if m is not None:
                id_ = m.group(1)

                # Force harmless default values to prevent any injection or jQuery problem
                dos_rule_enabled = True
                dos_rule_url = "/index.php"
                dos_rule_burst = 100
                dos_rule_thresold = 100
                dos_rule_timeout = 600

                try:
                    dos_rule_enabled = True if dataPosted.get('DOSRule_enable_'+id_) == 'on' else False
                    dos_rule_url = dataPosted['DOSRule_url_'+id_]
                    dos_rule_burst = dataPosted['DOSRule_burst_'+id_]
                    dos_rule_thresold = dataPosted['DOSRule_thresold_'+id_]
                    dos_rule_timeout = dataPosted['DOSRule_timeout_'+id_]
                except Exception as e:
                    pass

                dos_rule = ModSecDOSRules(dos_rule_enabled, dos_rule_url, dos_rule_burst, dos_rule_thresold, dos_rule_timeout)
                dos_rules.append(dos_rule)
    else:
        form = ModSecForm(None, instance=modsec)
        try:
            dos_rules = modsec.dos_rules
        except:
            dos_rules = []

    if request.method == 'POST' and form.is_valid():
        old_modsec = ModSec.objects.with_id(ObjectId(object_id))

        # 1) Remove old DOSRules
        if old_modsec and old_modsec.dos_rules:
            for dos_rule in old_modsec.dos_rules:
                dos_rule.delete()

        # 2) Create new DOSRules
        for dos_rule in dos_rules:
            dos_rule.save()

        modsec = form.save(commit=False)
        modsec.dos_rules = dos_rules

        if request.POST.get('block_desktops_ua', "off") == "on":
            modsec.ua_browser_anomaly_score = "999"
        else:
            modsec.ua_browser_anomaly_score = "0"

        if request.POST.get('block_crawler_ua', "off") == "on":
            modsec.ua_crawler_anomaly_score = "999"
        else:
            modsec.ua_crawler_anomaly_score = "2"

        if request.POST.get('block_suspicious_ua', "off") == "on":
            modsec.ua_unknown_anomaly_score = "999"
            modsec.ua_anonymous_anomaly_score = "999"
            modsec.ua_bot_anomaly_score = "999"
            modsec.ua_console_anomaly_score = "999"
            modsec.ua_emailclient_anomaly_score = "999"
            modsec.ua_emailharvester_anomaly_score = "999"
            modsec.ua_script_anomaly_score = "999"
        else:
            modsec.ua_unknown_anomaly_score = "2"
            modsec.ua_anonymous_anomaly_score = "2"
            modsec.ua_bot_anomaly_score = "2"
            modsec.ua_console_anomaly_score = "2"
            modsec.ua_emailclient_anomaly_score = "2"
            modsec.ua_emailharvester_anomaly_score = "2"
            modsec.ua_script_anomaly_score = "2"

        modsec.outbound_anomaly_score_threshold = modsec.inbound_anomaly_score_threshold

        modsec.save()
        config_modified.send(sender=ModSec, id=modsec.id)
        return HttpResponseRedirect('/firewall/modsec/#reload')

    return render_to_response('modsec_edit.html',
                              {'form': form, 'object_id': object_id, 'modsec': modsec, 'dos_rules': dos_rules},
                              context_instance=RequestContext(request))


@group_required('administrator', 'security_manager')
def edit_file(request, object_id=None):

    """ View dedicated to mod_security policy file edition

    :param object_id: MongoDB object_id of mod_security rule
    :param request: Django request object
    """

    # Retrieve content of the requested rule
    if request.method == 'GET' and object_id:
        rule = ModSecRules.objects.with_id(ObjectId(object_id))
        if rule:
            response = {}
            response['name'] = rule.name
            response['content'] = rule.rule_content
            return JsonResponse(response)

    # Update content of the requested rule
    elif request.method == 'POST' and object_id:
        rule = ModSecRules.objects.with_id(ObjectId(object_id))
        if rule:

            raw_data   = request.body
            try:
                data = json.loads(raw_data)
                content = data['content']
            except TypeError as e:
                return HttpResponseForbidden()
            except ValueError as e:
                return HttpResponseForbidden()

            rule.rule_content = content
            rule.save()
            response = {'status':'OK'}
            return JsonResponse(response)

    return HttpResponseForbidden()



@group_required('administrator', 'security_manager')
def import_scan(request, object_id=None):

    """ View dedicated to ModSecurity Rules Creation based on Scan results
    :param request: Django request object
    """

    form = ModSecScanForm(request.POST or None)
    log_info = None

    if request.method == 'POST':
        f = None
        parser_type = None
        buffer = ""

        try:
            f = request.FILES['file']
            parser_type = request.POST['type']
        except Exception as e:
            pass

        if f and parser_type in ["zap", "qualys", "acunetix_9"]:
            for chunk in f.chunks():
                buffer = buffer + chunk.decode('utf8')

            # We have results => Parse them and create ModSecurityRules
            results = scan_to_modsec(parser_type, buffer)
            if results:
                log_info = ""
                now = datetime.datetime.now()
                ts = now.strftime("%Y-%m-%d-%H%M")
                for app_name, data in results.items():

                    log_info = log_info + "<h2>Virtual Patching Status for application: '" + escape(app_name) + "'</h2>" + '<br/><br/>' + data[1]

                    # Create a new rules set
                    rs = ModSecRulesSet()
                    rs.type_rule = "virtualpatching"
                    rs.name = "["+str(ts)+"] Virtual patching - " + escape(app_name)
                    rs.save()

                    # Create the related rule
                    r = ModSecRules()
                    r.name = "custom.conf"
                    r.is_enabled = True
                    r.rs = rs
                    r.rule_content = data[0]
                    r.save()

                    conf = rs.get_conf()
                    rs.conf = conf
                    rs.save()

            else:
                log_info = "Sorry, something when wrong when parsing the XML report."
                logger.debug ("Something when wrong when parsing the XML report")


    # No file given, display the submit form
    return render_to_response('modsec_scan.html', {'form':form, 'log_info':log_info}, context_instance=RequestContext(request))


class TrustwaveDownload(Thread):
    def __init__(self, cluster, trustwave_user, trustwave_url):
        Thread.__init__(self)
        self.cluster = cluster
        self.trustwave_user = trustwave_user
        self.trustwave_url = trustwave_url
        self.result = {'status': True, 'message': ""}

    def run(self):
        try:
            modsec_id = self.get_modsec_id()
            modsec_headers = {
                'ModSec-unique-id': modsec_id,
                'ModSec-status': "{},{}".format(self.get_modsec_status(), modsec_id),
                'ModSec-key': self.trustwave_user
            }
            logger.debug("Downloading {}".format(self.trustwave_url))
            response = requests.get(self.trustwave_url, proxies=UpdateUtils.get_proxy_conf(), headers=modsec_headers)
            logger.info("Trustwave rules {} downloaded.".format(self.trustwave_url))
            content = response.content

            # Everything is ok, create a new rule set with a default name (can be changed after)
            rs = ModSecRulesSet()
            now = datetime.datetime.now()
            ts = now.strftime("%Y-%m-%d-%H%M")
            rs.name = "[" + str(ts) + "] TRUSTWAVE_SPIDERLABS"
            rs.type_rule = 'trustwave'
            """ We have to save the object, to reference-it in ModSecRules """
            rs.save()

            for match in re.findall("(https://dashboard.modsecurity.org/rules/resources/download/([^\"]+))\"", content):
                r = ModSecRules()
                r.rs = rs
                # Change the ruleset as data type, to not include it in apache conf
                r.name = '.'.join(match[1].split('.')[:-1] + ["data"])
                logger.debug("Downloading additionnal trustwave rules {} : {}".format(match[1], match[0]))
                r.rule_content = requests.get(match[0], proxies=UpdateUtils.get_proxy_conf(),
                                              headers=modsec_headers).content
                logger.info("Additionnal trustwave rules {} downloaded.".format(match[0]))
                # Enable the rule so it's written on disk
                r.is_enabled = True
                r.save()
                content = content.replace(match[0], r.filename)

            r = ModSecRules()
            r.rs = rs
            r.name = "Downloaded base rules"
            r.rule_content = content
            r.is_enabled = True
            r.save()

            rs.conf = rs.get_conf()
            rs.save()
            logger.info("[TRUSTWAVE] Ruleset '{}' successfully added.".format(rs.name))
            self.result['message'] = "[TRUSTWAVE] Ruleset '{}' successfully added.".format(rs.name)
        except Exception as e:
            self.result['status'] = False
            self.result['message'] = str(e)


    def get_modsec_id(self):
        return sha1("{}{}".format(':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2)),
                                  self.cluster.get_current_node().name)).hexdigest()

    def get_modsec_status(self):
        return "2.9.2,vulture,1.6.3/1.6.3,8.42/8.42 2018-03-20,(null),2.9.7"


@group_required('administrator', 'security_manager')
def import_crs(request, trustwave=None):

    """ View dedicated to mod_security OWASP Core Rule Set or Trustwave importation
    :param request: Django request object
    :param trustwave: If Set, import trustwave rules instead of CRS rules
    """

    cluster = Cluster.objects.get()
    system_settings = cluster.system_settings
    global_conf = system_settings.global_settings

    if trustwave:
        if not global_conf.trustwave_url or not global_conf.trustwave_user:
            import_msg = '#0 - Please configure Trustwave URL & Authentication token first'
            return render_to_response('modsec_rulesset.html', {'import_msg': import_msg}, context_instance=RequestContext(request))

        modsec_url = global_conf.trustwave_url
    else:
        modsec_url = global_conf.owasp_crs_url

    vulture_modsec_tmp_dir = "/tmp"
    file_name = vulture_modsec_tmp_dir + '/' + modsec_url.split('/')[-1]

    # Create Mod Security dir if it does not exist
    if not os.path.exists(vulture_modsec_tmp_dir):
        try:
            os.makedirs(vulture_modsec_tmp_dir)
        except OSError as e:
            import_msg = '#0 - Unable to create ModSecurity Directory. <br>Error is: ' + str(e.strerror)
            logger.error (import_msg + str(vulture_modsec_tmp_dir))
            return render_to_response('modsec_rulesset.html', {'import_msg': import_msg}, context_instance=RequestContext(request))

    # Clean previous download, if any
    if os.path.isfile(file_name):
        try:
            os.remove(file_name)
        except OSError as e:
            import_msg = '#0 - Unable to remove previous rules File. <br>Error is: ' + str(e.strerror)
            logger.error (import_msg + str(file_name))
            return render_to_response('modsec_rulesset.html', {'import_msg': import_msg}, context_instance=RequestContext(request))

    # Download the archive
    try:
        if trustwave:
            thread = TrustwaveDownload(cluster, global_conf.trustwave_user, global_conf.trustwave_url)
            logger.info("Starting download of trustwave rules.")
            thread.start()
            """ Try to retrieve the status of the thread """
            thread.join(15.0)
            if thread.isAlive():
                return HttpResponseRedirect('/firewall/modsec_rules/#downloading')
            else:
                if not thread.result.get('status'):
                    return render_to_response('modsec_rulesset.html', {'import_msg': thread.result.get('message')},
                                              context_instance=RequestContext(request))

            return HttpResponseRedirect('/firewall/modsec_rules/')

        else:
            r = requests.get(modsec_url, proxies=UpdateUtils.get_proxy_conf())

    except requests.exceptions.RequestException as e:
        import_msg = '#1 - Unable to download rules file. <br>Error is: ' + str(e.message)
        logger.error(import_msg + str(modsec_url))
        return render_to_response('modsec_rulesset.html', {'import_msg': import_msg}, context_instance=RequestContext(request))

    try:
        f = open(file_name, 'wb')
    except IOError as e:
        import_msg = '#2 - Unable to store rules file. <br>Error is: ' + str(e.strerror)
        logger.error (import_msg + str(file_name))
        return render_to_response('modsec_rulesset.html', {'import_msg': import_msg}, context_instance=RequestContext(request))

    for chunk in r:
        f.write(chunk)

    f.close()

    # If we are here, we assume that the download was OK
    # Next: unzip the file
    try:
        zfile = zipfile.ZipFile(file_name)
    except zipfile.BadZipfile:
        import_msg = '#3 - Unable to unzip rules file'
        logger.error (import_msg + str (file_name))
        return render_to_response('modsec_rulesset.html', {'import_msg': import_msg}, context_instance=RequestContext(request))

    # Be sure to use a unique directory for extraction
    extract_dir = tempfile.mkdtemp(dir=vulture_modsec_tmp_dir)
    zfile.extractall(extract_dir)

    # Everything is ok, create a new rule set with a default name (can be changed after)
    rs = ModSecRulesSet()
    now = datetime.datetime.now()
    ts  = now.strftime("%Y-%m-%d-%H%M")
    rs.name = "["+str(ts)+"] OWASP_CRS"
    rs.type_rule = 'crs'
    rs.save()

    # Ignore useless files in archives
    reg = re.compile('.*\.(conf|lua|data|txt)$')
    reg_ignore = re.compile(".*regression.*|.*\/util\/.*|.*activated_rules.*|.*README.*|.*INSTALL.*|.*CHANGES.*|.*gitignore.*|.*LICENSE.*|.*\.pdf$|.*\.c$|.*\.h$")

    path_match = re.match('https://github\.com/SpiderLabs/owasp-modsecurity-crs/archive/v([0-9|\.]+)/master\.zip', modsec_url)
    if os.path.exists(extract_dir+'/'+'owasp-modsecurity-crs-'+path_match.group(1)):
        p = 'owasp-modsecurity-crs-'+path_match.group(1)
    elif os.path.exists(extract_dir+'/'+'owasp-modsecurity-crs-'+path_match.group(1)+'-master'):
        p = 'owasp-modsecurity-crs-' + path_match.group(1)+'-master'
    else:
        logger.error("Could not find path for owasp rules : {}/{}".format(vulture_modsec_tmp_dir, modsec_url))

    for root, dirs, files in os.walk(extract_dir + '/' + p):
        for file in files:
            if not reg.match(file) or reg_ignore.match (root) or reg_ignore.match (file):
                continue

            path_file="%s/%s"%(root,file)
            # Create an entry for the rules
            try:
                with open(path_file, 'r') as content_file:
                    content = content_file.read()
            # This can happen if there is an antivirus on the host
            except IOError:
                logger.debug ("Unable to read file: " + str(path_file))
                pass

            r = ModSecRules()
            r.rs = rs
            r.name=path_file.replace(extract_dir + '/' + p, '')
            r.rule_content=content.replace("SecComponentSignature", "#SecComponentSignature")
            r.is_enabled=True
            r.save()

    conf = rs.get_conf()
    rs.conf = conf
    rs.save()

    return HttpResponseRedirect('/firewall/modsec_rules/')

@group_required('administrator', 'security_manager')
def clone_rules(request, object_id=None):

    """ View dedicated to mod_security rules set cloning

    :param object_id: MongoDB object_id of mod_security rules set
    :param request: Django request object
    """

    #Clone ruleset and rules
    modsec_rs   = ModSecRulesSet.objects.with_id(ObjectId(object_id))
    rules       = ModSecRules.objects.filter(rs = modsec_rs.id).order_by('name')

    modsec_rs.pk = None
    modsec_rs.name = 'Copy of ' + str (modsec_rs.name)
    modsec_rs.save()

    for rule in rules:
        rule.pk = None
        rule.rs = modsec_rs
        rule.save()

    conf = modsec_rs.get_conf()
    modsec_rs.conf = conf
    modsec_rs.save()

    if modsec_rs.type_rule == 'virtualpatching':
        return HttpResponseRedirect('/firewall/virtualpatching/')
    else:
        return HttpResponseRedirect('/firewall/modsec_rules/')


@group_required('administrator', 'security_manager')
def edit_rules(request, object_id=None):

    """ View dedicated to mod_security rules set management

    :param object_id: MongoDB object_id of mod_security rules set
    :param request: Django request object
    """

    modsec_rulesset = None
    #Retrieving access configuration
    if object_id:
        modsec_rulesset = ModSecRulesSet.objects.with_id(ObjectId(object_id))

    form = ModSecRulesSetForm(request.POST or None, instance=modsec_rulesset)

    # Saving information into database and redirect to policy list
    if request.method == 'POST' and form.is_valid():

        modsec_rs = form.save(commit=False)
        modsec_rs.save()
        config_modified.send(sender=ModSecRulesSet, id=modsec_rs.id)

        dataPosted = request.POST
        # Handle OWASP / TRSUWAVE or Custom selection
        if modsec_rs.type_rule in ('crs', 'trustwave', 'vulture', 'wlbl'):
            rules = ModSecRules.objects.filter(rs = modsec_rs).order_by('name')
            for rule in rules:
                rule.is_enabled = False
                rule_enabled = None

                try:
                    rule_enabled = dataPosted['rule_' + str(rule.id)]
                except Exception as e:
                    rule.save()
                    continue

                if rule_enabled:
                    rule.is_enabled = True
                rule.save()

        # Else, create or update the custom rules
        else:
            try:
                custom_rules =  dataPosted['custom_rules']
            except Exception as e:
                custom_rules = ""
                pass

            create=False
            try:
                rule = ModSecRules.objects.get(rs = modsec_rulesset)
            except Exception as e:
                create = True
                rule = ModSecRules()
                pass

            rule.rs = ModSecRulesSet.objects.with_id(ObjectId(modsec_rs.id))
            rule.name = "custom.conf"
            rule.rule_content = custom_rules
            rule.save()

        conf = modsec_rs.get_conf()
        modsec_rs.conf = conf
        modsec_rs.save()

        if modsec_rs.type_rule == 'virtualpatching':
            return HttpResponseRedirect('/firewall/virtualpatching/')
        else:
            return HttpResponseRedirect('/firewall/modsec_rules/')

    # Build the list of available / activated rules
    rules_list   = []
    custom_file  = None
    custom_rules = None
    is_crs       = False
    is_trustwave       = False
    is_crs_or_trustwave = False
    whitelist_or_blacklist = False

    if modsec_rulesset:
        if modsec_rulesset.type_rule in ('crs', 'trustwave', 'vulture'):
            is_crs_or_trustwave=True
            rules = ModSecRules.objects.filter(rs=modsec_rulesset).order_by('name')
            for rule in rules:
                rules_list.append(rule)

        elif modsec_rulesset.type_rule == 'wlbl':
            whitelist_or_blacklist = True
            try:
                rules = ModSecRules.objects.filter(rs=modsec_rulesset).order_by('name')
            except ModSecRules.DoesNotExist:
                rules = []

            for rule in rules:
                rule.rule_content = rule.rule_content.split('\n')
                rules_list.append(rule)

        # Load rule content for custom Rule, except if dataPosted exists
        else:
            # There can be only one rule
            try:
                rules = ModSecRules.objects.get(rs = modsec_rulesset)
                custom_rules = rules.rule_content
            except ModSecRules.DoesNotExist:
                custom_rules = ""

    # Override custom_rules with posted content, if any
    try:
        dataPosted = request.POST
        custom_rules = dataPosted['custom_rules']
    except Exception as e:
        pass

    if is_crs_or_trustwave:
        return render_to_response('modsec_rulesset_edit_crs.html',
                              {'form':form, 'object_id': object_id, 'modsec_rulesset':modsec_rulesset, 'rules_list':rules_list, 'custom_rules':custom_rules},
                              context_instance=RequestContext(request))
    elif whitelist_or_blacklist:
        return render_to_response('modsec_rulesset_edit_wlbl.html',
                            {'form': form, 'object_id': object_id, 'modsec_rulesset': modsec_rulesset, 'rules_list': rules_list, 'custom_rules': custom_rules},
                            context_instance=RequestContext(request))
    else:
        return render_to_response('modsec_rulesset_edit.html',
                              {'form':form, 'object_id': object_id, 'modsec_rulesset':modsec_rulesset, 'rules_list':rules_list, 'custom_rules':custom_rules},
                              context_instance=RequestContext(request))


@group_required('administrator', 'security_manager')
def add_rules_wl_bl(request):
    app_id        = request.POST['app_id']
    tmp_blacklist = request.POST['blacklist'].split('\n')
    tmp_whitelist = request.POST['whitelist'].split('\n')

    if tmp_blacklist[0] == "":
        tmp_blacklist = []
    if tmp_whitelist[0] == "":
        tmp_whitelist = []

    blacklist, whitelist = [], []
    app = Application.objects.with_id(ObjectId(app_id))
    for row in tmp_blacklist:
        blacklist.append(row.format(id="1"+str(uuid.uuid4().int)[0:6]))

    for row in tmp_whitelist:
        whitelist.append(row.format(id="1"+str(uuid.uuid4().int)[0:6]))

    if len(blacklist):
        blacklist_rule = ModSecRules(name=app.name, rs=app.wl_bl_rules, rule_content="\n".join(blacklist))
        blacklist_rule.save()

    if len(whitelist):
        whitelist_rule = ModSecRules(name=app.name, rs=app.wl_bl_rules, rule_content="\n".join(whitelist))
        whitelist_rule.save()

    app.wl_bl_rules.conf = app.wl_bl_rules.get_conf()
    app.wl_bl_rules.save()
    return JsonResponse({'done': True})

@group_required('administrator', 'security_manager')
def get_rules_wl_bl(request):
    app_id        = request.POST['app_id']
    log_id        = request.POST['log_id']
    rules, values = [], []

    app  = Application.objects.with_id(ObjectId(app_id))
    repo = app.log_custom.repository

    if repo.type_uri == 'mongodb':
        params       = {'type_logs': request.POST['type_logs']}
        mongo_client = MongoDBClient(repo)
        result       = mongo_client.search(params, id_query=log_id)['data']

    elif repo.type_uri == 'elasticsearch':
        elastic_client = ElasticSearchClient(repo)
        result         = elastic_client.search(id_query=log_id)
        result         = result['data']['hits']['hits'][0]['_source']

    temp_values = result.values()

    for val in temp_values:
        if isinstance(val, dict):
            [values.append(x) for x in val.values()]
        elif isinstance(val, list):
            [values.append(x) for x in val]
        else:
            values.append(val)

    for val in values:
        if val == "":
            continue

        try:
            for rule in ModSecRules.objects.filter(rs=app.wl_bl_rules, rule_content__contains=val):
                rules.append("{}|{}".format(rule.id, rule.rule_content))
        except:
            pass

    return JsonResponse({'rules': json.dumps(list(set(rules)))})
