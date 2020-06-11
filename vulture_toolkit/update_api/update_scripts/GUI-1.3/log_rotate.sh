#!/bin/sh

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/bin/echo "#!/home/vlt-gui/env/bin/python

import sys, os, logging, datetime

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vulture.settings')

import django
django.setup()

from vulture_toolkit.log.log_utils import LogRotate

log = LogRotate()
log.delete_logs()
" > /home/vlt-gui/crontab/monitor/log_rotate.hour
/bin/chmod +x /home/vlt-gui/crontab/monitor/log_rotate.hour


/bin/echo "[+] Installing logrotate packages"
if [ $(/usr/bin/whoami) = "root" ]
then
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install logrotate
    /bin/echo "[*] Installation ended successfully."
else
    /bin/echo "[/] You are not authorized to execute that file : only root can."
fi

if [ `/usr/bin/grep -c "'/usr/local/etc/logrotate.d/vulture.conf'," /home/vlt-sys/scripts/write_configuration_file` == 0 ]
then

/bin/echo "--- old	2016-09-01 15:49:44.840649000 +0200
+++ new	2016-09-01 15:51:17.749504000 +0200
@@ -39,6 +39,7 @@
                      '/usr/local/etc/pf.conf',
                      '/usr/local/etc/sentinel.conf',
                      '/usr/local/etc/fail2ban/jail.d/ssh-pf.conf',
+                     '/usr/local/etc/logrotate.d/vulture.conf',
                      '/etc/rc.conf.local',
                      '/etc/krb5.conf',
                      '/usr/local/etc/rsyslog.d/rsyslog.conf'," | patch /home/vlt-sys/scripts/write_configuration_file

fi

/bin/mkdir /usr/local/etc/logrotate.d
/usr/bin/touch /usr/local/etc/logrotate.d/vulture.conf
/bin/echo "\n/usr/local/sbin/logrotate /usr/local/etc/logrotate.d/vulture.conf" >> /home/vlt-sys/hour.sh


/bin/echo "--- old	2016-09-26 16:19:15.111261000 +0200
+++ new	2016-09-26 16:18:32.976813000 +0200
@@ -18,3 +18,4 @@
 vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/flush_keytab.sh
 vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/copy_keytab.sh
 vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/get_tgt
+vlt-sys ALL=NOPASSWD:/usr/local/sbin/logrotate" | patch /usr/local/etc/sudoers.d/vulture_sudoers