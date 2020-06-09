#!/bin/sh

echo 'weekly_acme_client_enable="YES"' > /etc/periodic.conf
echo 'weekly_acme_client_challengedir="/home/vlt-sys/Engine/acme-challenge"' >> /etc/periodic.conf
echo 'weekly_acme_client_renewscript="/home/vlt-gui/vulture/crontab/vlt-gui/acme-renew.py"' >> /etc/periodic.conf

mkdir -p /home/vlt-sys/Engine/acme-challenge/
chown vlt-sys:daemon /home/vlt-sys/Engine/acme-challenge/
chmod 750 /home/vlt-sys/Engine/acme-challenge/
