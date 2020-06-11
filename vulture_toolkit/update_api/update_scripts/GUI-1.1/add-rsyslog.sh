#!/bin/sh
#
# This migration script upgrades Vulture's package
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

env ASSUME_ALWAYS_YES=YES pkg install rsyslog-8.19.0

echo "syslogd_enable=\"NO\"" >> /etc/rc.conf
echo "rsyslogd_enable=\"YES\"" >> /etc/rc.conf
echo "rsyslogd_pidfile=\"/var/run/rsyslog.pid\"" >> /etc/rc.conf
echo "rsyslogd_config=\"/usr/local/etc/rsyslog.conf\"" >> /etc/rc.conf


echo '
module(load="imuxsock")
module(load="imklog")

$IncludeConfig /usr/local/etc/rsyslog.d/*.conf

security.*                                      /var/log/security
auth.info;authpriv.info                         /var/log/auth.log
mail.info                                       /var/log/maillog
lpr.info                                        /var/log/lpd-errs
ftp.info                                        /var/log/xferlog
cron.*                                          /var/log/cron
!-devd
*.=debug                                        /var/log/debug.log
*.emerg                                         *
!ppp
*.*                                             /var/log/ppp.log' > /usr/local/etc/rsyslog.conf

service syslogd onestop
service rsyslogd start

mkdir -p /var/db/loganalyzer
chown vlt-gui /var/db/loganalyzer
chmod 700 /var/db/loganalyzer