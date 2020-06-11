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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'System rc.conf Toolkit'

import os
import re
import subprocess

from django.conf import settings

from gui.models.network_settings import Listener
from gui.models.network_settings import Loadbalancer
from gui.models.ssl_certificate import SSLCertificate
from gui.models.system_settings import Cluster, PFSettings, IPSECSettings
from vulture_toolkit.system.sys_utils import write_in_file
from vulture_toolkit.templates import tpl_utils

import vulture_toolkit.system.http_pins as PKP


def check_status():
    """ Check if rc.conf.local need updates. Update file if needed

    :return: True if rc.conf.local was updated, False otherwise
    """
    listeners = []
    devices   = {}
    haproxy   = False
    reg       = re.compile("^ifconfig_([^ ]+)_alias\{\}.*")
    cluster   = Cluster.objects.get()
    node      = cluster.get_current_node()

    # We add alias number (by device)
    for listener in node.get_listeners():
            
        if reg.match(listener.rc_conf):
            dev = reg.match(listener.rc_conf).groups()[0]
            if not devices.get(dev):
                devices[dev] = 0
            cpt = devices.get(dev)
            rc_conf = listener.rc_conf.format(cpt)
            devices[dev] += 1
        else:
            rc_conf = listener.rc_conf
        listeners.append(rc_conf)

    """ GUI-0.3 Upgrade
      system_settings.pf_settings may not exists in GUI-0.3 upgraded from GUI-0.2
      In this case we need to initialize it with default VALUES
    """
    system_settings = node.system_settings
    if system_settings.pf_settings is None:
        system_settings.pf_settings = PFSettings()

    if system_settings.ipsec_settings is None:
        system_settings.ipsec_settings = IPSECSettings()

    loadbalancers = []
    for loadbalancer in Loadbalancer.objects.all():
        if loadbalancer.ssl_profile and loadbalancer.ssl_profile.hpkp_enable:
            loadbalancer.ssl_profile.pkp=PKP.getSPKIFingerpring(loadbalancer.ssl_profile.certificate.cert)

        if loadbalancer.incoming_listener.is_carp:
            for l in loadbalancer.incoming_listener.get_related_carp_inets():
                if l.get_related_node() == node:
                    haproxy = True
                    if loadbalancer not in loadbalancers:
                        loadbalancers.append(loadbalancer)

        elif loadbalancer.incoming_listener.get_related_node() == node:
            if loadbalancer not in loadbalancers:
                loadbalancers.append(loadbalancer)
            haproxy = True



    try:
        pf_logs = True if system_settings.pf_settings.repository_type == 'data' else False
    except KeyError:
        pf_logs = False

    parameters = {
        'default_ipv4_gw': node.default_ipv4_gw,
        'default_ipv6_gw': node.default_ipv6_gw,
        'static_route'   : node.static_route,
        'listeners'      : listeners,
        'pf_logs'        : pf_logs,
        'haproxy'        : haproxy,
        'strongswan'     : system_settings.ipsec_settings.enabled
    }

    # Checking if rc.conf.local differs.
    tpl, path_rc = tpl_utils.get_template('rc.conf.local')
    conf_rc = tpl.render(conf=parameters)
    try:
        with open(path_rc, 'r') as f:
            orig_conf = f.read()
    except IOError:
        orig_conf = ""

    # rc.conf.local and/or pf.conf differs => writing new version
    if orig_conf != conf_rc:
        write_in_file(path_rc, conf_rc)
        if node.default_ipv4_gw or node.default_ipv6_gw:
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                'service', 'routing', 'restart'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.communicate()


    #### HAPROXY Configuration ####
    parameters        = {'haproxy': loadbalancers}
    tpl, path_haproxy = tpl_utils.get_template('vlthaproxy')
    conf_haproxy      = tpl.render(conf=parameters)
    if not len(loadbalancers):
        conf_haproxy = ""
    try:
        with open(path_haproxy, 'r') as f:
            orig_conf = f.read()
    except IOError:
        orig_conf = ""

    ## Check diff in haproxy.conf
    proc = subprocess.Popen(["/usr/local/bin/sudo", "-u", "vlt-sys", "/usr/local/bin/sudo", 
        "service", "vlthaproxy", "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res, errors = proc.communicate()
    haproxy_need_start = "haproxy not running" in errors.decode('utf8')


    if haproxy and orig_conf != conf_haproxy:

        write_in_file(path_haproxy, conf_haproxy)

        """ Delete all certificates in /home/vlt-sys/Engine/conf/haproxy """
        os.system("/bin/rm %shaproxy/*" % settings.CONF_DIR)

        """ Write SSL-Profile certificates """
        for loadbalancer in loadbalancers:
            if loadbalancer.enable_tls and loadbalancer.ssl_profile:
                loadbalancer.ssl_profile.write_HAProxy_conf()

        """ Store certificates so that HA-PROXY may use them """
        for cert in SSLCertificate.objects():
            cert.write_certificate()

        if not haproxy_need_start:

            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
            'service', 'vlthaproxy', 'restart'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.communicate()

        else:

            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                'service', 'vlthaproxy', 'start'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.communicate()

    elif haproxy and haproxy_need_start:

        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                'service', 'vlthaproxy', 'start'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.communicate()

    elif not haproxy:

        write_in_file(path_haproxy, conf_haproxy)
        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
            'service', 'vlthaproxy', 'stop'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.communicate()



    cluster = Cluster.objects.get()
    node = cluster.get_current_node()

    ## CHECK Vulture Cluster Whitelist for Packet Filter
    ips = []
    for listener in Listener.objects.all():
        ips.append(listener.ip)
    ips = set(ips)


    proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', 'pfctl', '-t', 'vulture_cluster', '-T', 'show'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res, errors = proc.communicate()
    if res is False:
        return False
    res = res.decode('utf8')

    for ip in ips:
        if ip not in node.system_settings.pf_settings.pf_whitelist:
            node.system_settings.pf_settings.pf_whitelist = node.system_settings.pf_settings.pf_whitelist + '\n' + str(ip)

    node.save(bootstrap=True)
    res = [r.strip() for r in res.split('\n') if r != ""]
    for ip in ips:
        if ip not in res:
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', 'pfctl', '-t', 'vulture_cluster', '-T', 'add', ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res2, errors = proc.communicate()
            if res2 is False:
                return False

    return True
