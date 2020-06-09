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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'System kerberos conf Toolkit'

import logging
import subprocess

from gui.kerberos_backend import KerberosBackend
from gui.models.repository_settings import BaseAbstractRepository
from vulture_toolkit.auth.kerberos_client import import_keytab
from vulture_toolkit.auth.kerberos_client import test_keytab
from vulture_toolkit.system.sys_utils import write_in_file
from vulture_toolkit.templates import tpl_utils

logger = logging.getLogger('services_events')


def check_status():
    """ Check if krb5.conf need updates. Update file if needed

    :return: True if krb5.conf was updated, False otherwise
    """
    # No matter if keytab need update : Do it !
    # First ; Clear file  (don't delete to not change permissions)
    try:
        proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                                 '/home/vlt-sys/scripts/flush_keytab.sh'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        res, errors = proc.communicate()
        logger.debug("CONF::Kerberos: Flushing keytab stdout: {}".format(str(res)))
        if errors:
            logger.error("CONF::Kerberos: Flushing keytab error: {}".format(str(errors)))
    except Exception as e:
        logger.error("CONF::Kerberos: Flushing keytab error: {}".format(str(e)))

    # retrieve the Kerberos repositories to generate the configuration file and the keytab
    krb5_repos = list()
    repo_list = BaseAbstractRepository.get_auth_repositories()
    for repo in repo_list:
        if isinstance(repo.get_backend(), KerberosBackend):
            # Don't write bullshit in system files
            if test_keytab(repo.keytab)['status'] :
                # Retrieve keytabs from repos and import them into master keytab
                result = import_keytab(logger, repo.keytab)
                if not result:
                    logger.error("CONF::Kerberos: Fail to import keytab for repository : {}".format(str(repo.repo_name)))
                else:
                    logger.info(
                        "CONF::Kerberos: Successfully imported keytab for repository : {}".format(str(repo.repo_name)))
            else:
                logger.error("CONF::Kerberos: Unable to decode the keytab : write_on_system not allowed.")

            # And other attributes needed to generate the configuration file
            krb5_repo = dict()
            krb5_repo['realm'] = repo.realm
            if str(repo.domain_realm)[0] == '.':
                krb5_repo['domain'] = str(repo.domain_realm)[1:]
            else:
                krb5_repo['domain'] = repo.domain_realm
            krb5_repo['kdcs'] = str(repo.kdc).split(',')
            krb5_repo['admin_server'] = repo.admin_server

            krb5_repos.append(krb5_repo)

    if len(krb5_repos) > 0 :
        # Get required fields to generate the template with Kerberos Repositories
        parameters = {
            'default_realm': krb5_repos[0]['realm'],
            'repos': krb5_repos,
        }

        # Generate the configuration with template and repositories retrieved
        tpl, path_rc = tpl_utils.get_template('kerberos')
        conf_rc = tpl.render(conf=parameters)

        try:
            f = open(path_rc, 'r')
            orig_conf = f.read()
        except IOError:
            orig_conf = ""

        # If krb5.conf and newly generated conf differs => writing new version
        if orig_conf != conf_rc:
            write_result = write_in_file(path_rc, conf_rc)
            return True
        else:
            return False

    return False
