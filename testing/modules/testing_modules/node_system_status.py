import glob
import grp
import os
import pwd
import sys
import time

import django
import redis

from testing.core.testing_module import TestingModule
sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')
django.setup()

from gui.models.monitor_settings import Monitor
import subprocess

class Module(TestingModule):

    def __str__(self):
        return "Node System Status"

    def __init__(self):
        super(Module, self).__init__()
        self.log_level = 'warning'

    @staticmethod
    def pf_memory_limit():
        """
        Verify the number of time we reached the PF memory counter
        """
        try:
            pf_stats = subprocess.check_output(['/usr/local/bin/sudo -u vlt-sys /usr/local/bin/sudo /sbin/pfctl -si | /usr/bin/grep "memory" | /usr/bin/awk \'{print $2}\''], shell=True)
            result = pf_stats.decode('utf8').rstrip()
        except:
            pass

        assert (result == "0"), "PF Memory limit reached: to much entries in state table"

    @staticmethod
    def root_disk_space():
        """
        Verify the amount of space left on the root disk
        """
        try:
            monitor = Monitor.objects.order_by('-date').first()
        except:
            pass
        assert (monitor.root_percent < 80), "Root disk almost full ({} %)".format(monitor.root_percent)

    @staticmethod
    def home_disk_space():
        """
        Verify the amount of space left on the home disk
        """
        try:
            monitor = Monitor.objects.order_by('-date').first()
        except:
            pass
        assert (monitor.home_percent < 80), "Home disk almost full ({} %)".format(monitor.home_percent)

    @staticmethod
    def var_disk_space():
        """
        Verify the amount of space left on the var disk
        """
        try:
            monitor = Monitor.objects.order_by('-date').first()
        except:
            pass
        assert (monitor.var_percent < 80), "Var disk almost full ({} %)".format(monitor.var_percent)

    @staticmethod
    def reputation_database():
        """
        Verify the reputation database
        """
        redis_cli = redis.StrictRedis(unix_socket_path='/var/db/redis/redis.sock', db=0, decode_responses=True)
        res = redis_cli.execute_command('ROLE')
        if 'master' in res:
            assert (abs(os.path.getmtime("/var/db/loganalyzer/ip-reputation.mmdb") - time.time()) < 24 * 3600), "Reputation database needs to be updated !"
        else:
            assert (True)

    @staticmethod
    def files_permission():
        """
        Verify the permissions set on specific files and directories
        """

        problem = False
        problems = ""

        matrix = {
            '/home/vlt-sys/Engine/conf/certs'                    : (775, 'vlt-sys', 'vlt-conf'),
            '/home/vlt-sys/Engine/conf/haproxy'                  : (770, 'vlt-gui', 'daemon'),
            '/home/vlt-sys/Engine/conf/haproxy/*'                : (640, 'vlt-gui', 'daemon'),
            '/usr/local/bin/free'                                : (555, None, None),
            '/usr/local/etc/rsyslog.d/'                          : (755, None, None),
            '/usr/local/etc/ssmtp/'                              : (755, 'root', 'ssmtp'),
            '/usr/local/etc/logrotate.d/vulture.conf'            : (644, 'root', 'wheel'),
            '/home/vlt-sys/scripts/*'                            : (550, None, None),
            '/usr/local/etc/rc.d/*'                              : (555, None, None),
            '/home/vlt-gui/*.sh'                                 : (500, None, None),
            '/home/vlt-sys/*.sh'                                 : (500, None, None),
            '/home/vlt-sys/recover/'                             : (770, 'vlt-sys', 'vlt-sys'),
            '/etc/krb5.keytab'                                   : (640, 'root', 'vlt-portal'),
            '/home/vlt-gui/'                                     : (751, 'vlt-gui', 'vlt-gui'),
            '/home/vlt-adm/'                                     : (751, 'vlt-adm', 'vlt-adm'),
            '/var/bootstrap/bootstrap.py'                        : (700, None, None),
            '/var/db/loganalyzer/'                               : (700, 'vlt-gui', None),
            '/var/log/pflog.log'                                 : (644, None, None),
            '/usr/local/etc/pf.conf'                             : (644, None, None),
            '/usr/local/etc/pf.abuse.conf'                       : (644, 'vlt-gui', None),
            '/usr/local/etc/pf.vulturecluster.conf'              : (644, 'vlt-gui', None),
            '/usr/local/etc/vlthaproxy.conf'                     : (644, None, None),
            '/home/vlt-sys/'                                     : (None, 'vlt-sys', 'vlt-sys'),
            '/var/log/Vulture'                                   : (None, 'vlt-gui', 'vlt-web'),
            '/var/log/Vulture/portal'                            : (None, 'vlt-portal', 'vlt-web'),
            '/home/vlt-sys/Engine/conf/SSL*'                     : (640, 'vlt-gui', 'daemon'),
            '/home/vlt-sys/Engine/conf/acme-challenge/'          : (750, 'vlt-sys', 'daemon'),
            '/home/vlt-gui/vulture/crontab/vlt-gui/acme-renew.py': (500, 'vlt-gui', None),
            '/var/db/useragent/'                                 : (750, 'vlt-gui', 'vlt-web'),
            '/var/db/useragent/regexes.yaml'                     : (644, 'vlt-gui', 'vlt-web')
        }

        for k,v in matrix.items():
            expected_mode  = v[0]
            expected_user  = v[1]
            expected_group = v[2]

            if '*' in k:
                for file in glob.glob(k):
                    try:
                        st    = os.stat(file)
                        user  = pwd.getpwuid(st.st_uid).pw_name
                        group = grp.getgrgid(st.st_gid).gr_name
                        mode  = int(oct(st.st_mode)[-3:])

                        if expected_mode and mode != expected_mode:
                            proc     = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', '/bin/chmod', str(expected_mode), file], stdout=subprocess.PIPE)
                            problems = problems+str(file)+' do not have correct permissions: ({} instead of {}). Automaticaly fixed.'.format(mode, expected_mode)+'\n'
                            problem  = True

                        if expected_user and user != expected_user:
                            proc     = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', '/usr/sbin/chown', expected_user+":", file], stdout=subprocess.PIPE)
                            problems = problems+str(file)+' do not have correct ownership: ({} instead of {}). Automaticaly fixed.'.format(user, expected_user)+'\n'
                            problem  = True

                        if expected_group and group != expected_group:
                            proc     = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', '/usr/bin/chgrp', expected_group, file], stdout=subprocess.PIPE)
                            problems = problems+str(file)+' do not have correct group ownership: ({} instead of {}). Automaticaly fixed.'.format(group, expected_group)+'\n'
                            problem  = True

                    except Exception as e:
                        pass
            else:
                try:
                    st    = os.stat(k)
                    user  = pwd.getpwuid(st.st_uid).pw_name
                    group = grp.getgrgid(st.st_gid).gr_name
                    mode  = int(oct(st.st_mode)[-3:])

                    if expected_mode and mode != expected_mode:
                        proc     = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', '/bin/chmod', str(expected_mode), k], stdout=subprocess.PIPE)
                        problems = problems+str(k)+' do not have correct permissions: ({} instead of {}). Automaticaly fixed.'.format(mode, expected_mode)+'\n'
                        problem  = True

                    if expected_user and user != expected_user:
                        proc     = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', '/usr/sbin/chown', expected_user+":", k], stdout=subprocess.PIPE)
                        problems = problems+str(k)+' do not have correct ownership: ({} instead of {}). Automaticaly fixed.'.format(user, expected_user)+'\n'
                        problem  = True

                    if expected_group and group != expected_group:
                        proc     = subprocess.Popen(['/usr/local/bin/sudo', '-u', 'vlt-sys', '/usr/local/bin/sudo', '/usr/local/bin/sudo', '/usr/bin/chgrp', expected_group, k], stdout=subprocess.PIPE)
                        problems = problems+str(k)+' do not have correct group ownership: ({} instead of {}). Automaticaly fixed.'.format(group, expected_group)+'\n'
                        problem  = True

                except Exception as e:
                    pass


        assert (problem is False), "{}".format(problems)
