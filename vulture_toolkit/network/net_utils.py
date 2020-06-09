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
__author__ = "Florian Hagniel, Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Network validator toolkit'

import re
import socket
import subprocess
from threading import Timer

import ipaddress
import pexpect


def is_valid_hostname(hostname):
    """ Function used to validate an hostname syntax (RFC 1123)

        :param hostname : hostname to check
        :returns: True if pattern match, False otherwise
    """
    pattern = "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
    reg = re.compile(pattern)
    if reg.match(hostname):
        return True
    else:
        return False


def is_resolvable_hostname(hostname):
    """ Function used to test if an hostname is DNS resolvable

        :param hostname : hostname to check
        :returns: True if we have DNS info, False otherwise
    """
    try:
        socket.getaddrinfo(hostname, None)
        return True
    except socket.gaierror:
        return False


def make_hostname_resolvable(hostname, ip):
    """Add hostname/IP to /etc/hosts in order to make
    hostname resolvable. If hostname is already define, its IP is replaced

    :param hostname: name of host
    :param ip: ip address of host
    :return:
    """
    proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                             '/home/vlt-sys/scripts/add_to_etc_hosts',
                             hostname, ip], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    res, errors = proc.communicate()
    if not errors:
        return True
    else:
        return False#TODO ?? Log


def is_valid_ip_address(ip_addr):
    """ Function used to test if an IP Address (v4 or v6) is valid

        :param ip_addr : ip_address to verify
        :returns: True if valid, False otherwise
    """
    try:
        ipaddress.ip_address(ip_addr)
        return True
    except Exception:
        return False


def get_hostname():
    """ Function used to get hostname of the current host

        :returns: A string containing the hostname
    """
    hostname = subprocess.check_output(['hostname']).decode('utf8').strip()
    return hostname


def is_running(ip_addr, port):
    """ Function used to check if something is listening on a given IP / PORT

    :param ip_addr: the IP Address of the listening process
    :param port: the TCP port of the listening process
    :return: True of False or None in case of an error
    """
    proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', '/usr/bin/netstat', '-an', '-W', '-p', 'tcp'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc_grep = subprocess.Popen(['/usr/bin/grep', 'LISTEN'],stdin=proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res, errors = proc_grep.communicate()

    if errors:
        return None

    if str(ip_addr) == "0.0.0.0":
        ip_address = "\*"
    else:
        ip_address = ipaddress.ip_address(ip_addr)
    reg = re.compile(str(ip_address) + '\.' + str(port), re.M)
    running = reg.findall(res.decode('utf8'))
    if running:
        return True

    return False

def kill (p):
    try:
        p.kill()
    except OSError:
        pass


def start(ip_addr, port, passphrases={}):
    """ Function used to start a Vulture Apache process on a given IP / PORT

    :param ip_addr: the IP Address of the  process
    :param port: the TCP port of the  process
    :param passphrases: None or a dict with passphrase for private key used in add (Dict is: listener_{{id}} / passphrase)
        Passphrase cannot be set from command line
        That's why Listener with passphrase won't start during service Vulture restart or reboot
         It is not a bug, it's a feature ;-)
    :return: True if success or a string with error message otherwise
    """
    try:

        import logging
        logger = logging.getLogger('local_listeners')
        pass_phrase = None

        config_file = '/home/vlt-sys/Engine/conf/{}-{}.conf'.format(ip_addr, port)

        cmd = '/usr/local/bin/sudo -u vlt-sys /usr/local/bin/sudo ' \
                  '/home/vlt-sys/Engine/bin/httpd -f {} -t'.format(config_file)

        """ Before doing anything, check if the configuration file is good """
        child = pexpect.spawn(cmd, timeout=20)
        index = child.expect(["Syntax OK", pexpect.EOF])
        if index != 0:
            msg = child.before
            err = "<br/>{}".format(str(msg))
            logger.error(msg)
            return err

        cmd = '/usr/local/bin/sudo -u vlt-sys /usr/local/bin/sudo ' \
                  '/home/vlt-sys/Engine/bin/httpd -f {} -k start'.format(config_file)


        """ No Passphrase provided """
        if not passphrases:
            proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys',
                                 '/usr/local/bin/sudo', '/home/vlt-sys/Engine/bin/httpd',
                                 '-f', config_file, '-k', 'start'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            """ We set a 3 seconds timeout because, from shell, Apache will wait forever for passphrases, if any """
            t = Timer(3, kill,[proc])
            t.start()
            if proc.wait() != 0:
                t.cancel()
                err = "Listener {}:{} did not start (Int: Passphrase needed ?)".format(ip_addr, port)
                logger.error(err)
                return err
            else:
                logger.info("Listener {}:{} successfully "
                            "started".format(ip_addr, port))
                return True

    except Exception as e:
        logger.error(e)
        return e

    """ A passphrase is required """
    try:

        """ Apache will ask for the password of the private key contained in a pem file
            We need to catch in prompt:
                - The application's name, for logging purposes
                - The certificate_id, contained in the certificateKeyFile's name
        """
        reg = re.compile("Private key (.*) \(.*SSLCertificateKeyFile-(.*).txt")

        child = pexpect.spawn(cmd, timeout=15)
        index = child.expect(["Enter pass phrase:", pexpect.EOF])
        #We catch 'Enter pass phrase:'
        if index == 0:

            while (True):

                """ Catch Apache prompt asking for passphrase """
                prompt_text = child.before

                """ Capture app_name and certificate_id """
                matched_id = reg.search(prompt_text)
                if matched_id:
                    cert_id = matched_id.groups()[1]
                    app_name = matched_id.groups()[0]
                    pass_phrase = passphrases.get('ssl_{}'.format(cert_id))
                else:
                    """ If we can't find a valid regex: there is a problem
                        Just break
                    """
                    logger.error("Unable to find app_id or cert_id for passphrase for application '{}'.".format(app_name))
                    break


                """ Send passphrase to Apache """
                child.sendline(pass_phrase)

                """ And check if this passphrase is the good one """
                pass_confirm_dialog = child.expect(["OK: Pass Phrase Dialog successful.",
                                                "Apache:mod_ssl:Error: Pass phrase incorrect"])

                """ Cool, it was a good passphrase !
                    Our job is not finished yet, because Apache may be asking for another passphrase for another application
                    Indeed, A Listener may contains several VirtualHost, with several private keys
                """
                if pass_confirm_dialog == 0:
                    logger.info("Successful pass phrase for application '{}'".format(app_name))
                    index = child.expect(["Enter pass phrase:", pexpect.EOF])
                    """ Another passphrase is required, let's loop """
                    if index == 0:
                        continue
                    elif index == 1:
                        logger.info("Listener {}:{} successfully started".format(ip_addr, port))
                        return True
                elif pass_confirm_dialog == 1:
                    logger.warning("Bad passphrase for application '{}'".format(app_name))
                    return "Passphrase incorrect for application '{}'".format(app_name)

    except Exception as e:
        logger.error("An unexpected error has occurred during Apache startup")
        logger.exception(e)
        return str(e)



def stop(ip_addr, port):
    """ Function used to stop a Vulture Apache process on a given IP / PORT

    :param ip_addr: the IP Address of the  process
    :param port: the TCP port of the  process
    :return: True of False or None in case of an error
    """
    import logging
    logger = logging.getLogger('local_listeners')
    config_file = '/home/vlt-sys/Engine/conf/{}-{}.conf'.format(ip_addr, port)
    proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys',
                             '/usr/local/bin/sudo', '/home/vlt-sys/Engine/bin/httpd',
                             '-f', config_file, '-k', 'stop'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res, errors = proc.communicate()
    if not errors:
        logger.info("Listener {}:{} successfully "
                    "stopped".format(ip_addr, port))
        return True
    else:
        logger.error("An error has occurred during Apache stop, "
                     "error: {}".format(errors))
        return errors


def graceful(ip_addr, port):
    """ Function used to gracefully restart a Vulture Apache process on a given IP / PORT

    :param ip_addr: the IP Address of the  process
    :param port: the TCP port of the  process
    :return: True of False or None in case of an error
    """
    config_file = '/home/vlt-sys/Engine/conf/{}-{}.conf'.format(ip_addr, port)
    proc = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo',
                             '/home/vlt-sys/Engine/bin/httpd',
                             '-f', config_file, '-k', 'graceful'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res, errors = proc.communicate()

    if len(errors):
        return False, errors

    return True, None
   
def get_devices():
    """ Get list of network devices (em0,lo0 ..)

        :returns: A list of string containing network device name
    """
    reg = re.compile('^(.*):\s+flags=.*', re.M)
    proc = subprocess.Popen(["/sbin/ifconfig"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    res = proc.communicate()
    success = res[0].decode('utf8')
    # Fill in list
    device_lst = reg.findall(success)

    return device_lst



