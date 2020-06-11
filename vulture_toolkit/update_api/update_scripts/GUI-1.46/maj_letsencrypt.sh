#!/bin/sh

/bin/echo "Installing Let's encrypt package"

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install acme-client

echo 'weekly_acme_client_enable="YES"' >> /etc/periodic.conf
echo 'weekly_acme_client_challengedir="/home/vlt-sys/acme-challenge"' >> /etc/periodic.conf
echo 'weekly_acme_client_renewscript="/home/vlt-gui/vulture/crontab/vlt-gui/acme-renew.py"' >> /etc/periodic.conf

mkdir -p /home/vlt-sys/acme-challenge/
chown vlt-sys:daemon /home/vlt-sys/acme-challenge/
chmod 750 /home/vlt-sys/acme-challenge/

