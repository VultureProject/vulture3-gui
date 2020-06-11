#!/bin/sh
#
# This migration script install fail2ban 
# Add support for fail2ban template in /home/vlt-sys/scripts/write_configuration_file
# Enable fail2ban in the rc.conf file
#

. /etc/rc.conf

/bin/echo "[+] Installing fail2ban packages"

if [ $(/usr/bin/whoami) = "root" ]
then
    if [ "$http_proxy" != "" ]
    then
        export https_proxy="http://$http_proxy"
        export http_proxy="http://$http_proxy"
    fi
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install py27-fail2ban
    /bin/echo "[*] Installation ended successfully."
else
    /bin/echo "[/] You are not authorized to execute that file : only root can."
fi


val=`/bin/cat /home/vlt-sys/scripts/write_configuration_file | /usr/bin/grep "'/usr/local/etc/fail2ban/jail.d/ssh-pf.conf',"`
if [ "$val" == "" ]
then

	/bin/echo "--- old	2016-08-08 15:20:55.518149000 +0200
+++ new	2016-08-02 14:09:55.295532000 +0200
@@ -37,6 +37,7 @@
                      '/usr/local/etc/fluentd/fluent.conf',
                      '/usr/local/etc/redis.conf',
                      '/usr/local/etc/pf.conf',
+                     '/usr/local/etc/fail2ban/jail.d/ssh-pf.conf',
                      '/usr/local/etc/sentinel.conf',
                      '/etc/rc.conf.local',
                      '/etc/krb5.conf'," | patch /home/vlt-sys/scripts/write_configuration_file

fi

val=`/bin/cat /etc/rc.conf | /usr/bin/grep 'fail2ban_enable="YES"'`
if [ "$val" == "" ]
then
	/bin/echo 'fail2ban_enable="YES"' >> /etc/rc.conf
fi