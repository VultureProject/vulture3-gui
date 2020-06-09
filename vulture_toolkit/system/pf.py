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
__doc__ = 'PF Toolkit'

import re
import subprocess
import sys

sys.path.append("/home/vlt-gui/vulture")

import logging
import logging.config

from vulture_toolkit.system.service_base import ServiceBase
from vulture_toolkit.system import rc_conf
from gui.models.system_settings import Cluster
from django.template import Context, Template

logger = logging.getLogger('services_events')


class PF(ServiceBase):

    def __init__ (self):
        self.service_name = 'pf'


    def status(self, parameters=None):
        """ Service status

        :returns: True if sshd is running, False otherwise
        """
        # Executing service service_name status as vlt-sys user
        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                 'service', self.service_name, 'onestatus'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        success, error = proc.communicate()
        if success:
            m = re.match('Status: Disabled', success.decode('utf8'))
            if m is None:
                status="UP"
            else:
                status="DOWN"
        else:
            """ service pf status throws an error if pf_enable is not
            set to True in rc.conf. This is because a kernel module
            needs to be loaded.
            """
            status="ERROR"

        """ Retrieve active blacklist """
        pf_current_blacklist=""
        if status is "UP":
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                     '/sbin/pfctl', '-t', 'abusive_hosts', '-T', 'show'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res = proc.communicate()
            pf_current_blacklist = res[0].decode('utf8')

        """ Retrieve active whitelist (vulture's cluster members) """
        pf_current_whitelist=""
        if status is "UP":
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                     '/sbin/pfctl', '-t', 'vulture_cluster', '-T', 'show'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res = proc.communicate()
            pf_current_whitelist = res[0].decode('utf8')

        """ Retrieve current policy """
        pf_current_policy=""
        if status is "UP":
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                     '/sbin/pfctl', '-sr'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res = proc.communicate()
            pf_current_policy = res[0].decode('utf8')


        bl=dict()
        bl['pf_current_blacklist']=pf_current_blacklist
        bl['pf_current_whitelist']=pf_current_whitelist
        bl['pf_current_policy']=pf_current_policy

        return (status, bl)


    def start_service(self,check=True):
        """ Start Service
        :returns: True if success, False otherwise
        """

        """ /etc/rc.conf needs to be updated with appropriate configuration """
        if check:
            rc_conf.check_status()

        """ Don't start anything if pf is not enable on the host """
        cluster = Cluster.objects.get()
        node = cluster.get_current_node()
        system_settings = node.system_settings

        """ GUI-0.3 Upgrade
        system_settings.pf_settings may not exists in GUI-0.3 upgraded from GUI-0.2
        In this case we need to return (click 'Save' first)
        """
        if not system_settings.pf_settings:
            logger.info("{} configuration not saved. Won't start it".format(self.service_name))
            return False

        """ Executing service service_name onestart as vlt-sys user """
        subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo',
                                 '/usr/bin/touch', '/usr/local/etc/pf.abuse.conf'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo',
                                 '/usr/sbin/chown', 'vlt-gui', '/usr/local/etc/pf.abuse.conf'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)


        with open('/usr/local/etc/pf.abuse.conf','w') as bl:
            bl.write(node.system_settings.pf_settings.pf_blacklist)

        with open('/usr/local/etc/pf.vulturecluster.conf','w') as bl:
            bl.write(node.system_settings.pf_settings.pf_whitelist)

        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                     '/sbin/pfctl', '-e'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)


        success, error = proc.communicate()
        error = error.decode('utf8')
        if success or "pf enabled" in error:
            logger.info("{} service enable".format(self.service_name))
            ok=True
        elif "already enable" in error:
            logger.info("{} service already enable".format(self.service_name))
            ok=True
        else:
            logger.error("PF enable service: '{}'".format (error))
            ok=False


        if ok and system_settings.pf_settings.repository_type == 'data':

            logger.info("Trying to start {} service".format(self.service_name))
            """ Starting pflogs service """
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                             'service', "pflog", 'onestart'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            success, error = proc.communicate()

            if success:
                logger.info("pflog service started")
                return True
            elif error:
                logger.error(error)
                return False
            else:
                return_code = proc.returncode
                if return_code == 0:
                    logger.info("pflog service started")
                    return True

        return ok


    def stop_service(self,check=True):
        """ Stop Service
        :returns: True if success, False otherwise
        """

        """ /etc/rc.conf needs to be updated with appropriate configuration """
        if check:
            rc_conf.check_status()

        cluster = Cluster.objects.get()
        node = cluster.get_current_node()
        system_settings = node.system_settings

        """ Executing service service_name onestart as vlt-sys user """
        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                     '/sbin/pfctl', '-d'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        success, error = proc.communicate()

        if success or "pf disabled" in error:
            logger.info("{} service disable".format(self.service_name))
            ok=True
        elif "pf not enable" in error:
            logger.info("{} service already disable".format(self.service_name))
            ok=True
        else:
            logger.error("PF disable service: '{}'".format (error))
            ok=False


        if ok and system_settings.pf_settings.repository_type == 'data':
            """ Starting pflogs service """
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                             'service', "pflog", 'onestart'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            success, error = proc.communicate()
            if success:
                logger.info("pflog service stopped")
                return True
            elif error:
                logger.error(error)
                return False
            else:
                return_code = proc.returncode
                if return_code == 0:
                    logger.info("pflog service stopped")
                    return True

        return ok


    def restart_service(self):
        """ Reload pf Service
        :returns: True if success, False otherwise
        """

        """ /etc/rc.conf needs to be updated with appropriate configuration """
        rc_conf.check_status()

        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                             '/sbin/pfctl', '-f', '/usr/local/etc/pf.conf'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        success, error = proc.communicate()

        if error:
            logger.error("PF: Error when applying rules: {} ".format (error))
        else:
            logger.info("PF configuration reloaded")

        """ Start the service, if needed """
        return self.start_service(check=False)



    def write_configuration(self, settings, service_settings=None):

        try:
            template = Template("""
pass quick on lo0 all
block in log all
pass in proto icmp6 all
pass out proto icmp6 all
pass out all keep state

table <vulture_cluster> persist file "/usr/local/etc/pf.vulturecluster.conf"
pass in quick from <vulture_cluster>

table <abusive_hosts> persist file "/usr/local/etc/pf.abuse.conf"
block in log quick from <abusive_hosts>

{% for rule in conf.pf_rules %}# --- {{rule.comment}}
{{rule.action}} {{rule.direction}} {% if rule.log %}log {% endif %}quick {% if rule.interface != 'any' %}on {{rule.interface}} {% endif %}{%if rule.inet %}{{rule.inet}} {% endif %} {% if rule.protocol and rule.protocol != "any" %}proto {{rule.protocol}} {% endif %}{% if rule.source %}from {{rule.source}}{% endif %} {% if rule.destination or rule.port %}to {% endif %} {{rule.destination}} {% if rule.port %}port {{rule.port}} {% endif %} {{rule.flags}} {% if rule.rate %}(max-src-conn-rate {{rule.rate}},overload <abusive_hosts> flush global){% endif %}
{% endfor %}""")
        except Exception as e:
            logger.error ("PF Template error: {}".format (str(e)))
            return False

        temp = template.render(Context({'conf': settings}))

        settings_txt = Template("""#PF global limits
set limit { states {{conf.pf_limit_states}}, frags {{conf.pf_limit_frags}}, src-nodes {{conf.pf_limit_src}} }
""").render(Context({'conf': settings})) + \
                       Template(settings['pf_rules_text']).render(Context({'rule': temp}))
        super(PF, self).write_configuration(settings_txt, service_settings)
