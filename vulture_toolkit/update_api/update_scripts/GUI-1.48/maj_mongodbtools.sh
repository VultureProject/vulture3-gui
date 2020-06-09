#!/bin/sh
#
# This migration script install mongodb32-tools package
#
#
/bin/echo "[*] Installing MongoDB tools package"

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install mongodb32-tools >>/tmp/installation.log 2>&1

/bin/echo "#!/bin/sh

touch /var/log/Vulture/gui/redis_events.log
chown vlt-gui:vlt-web /var/log/Vulture/gui/*
/usr/local/bin/sudo /home/vlt-sys/scripts/check_updates.hour
sudo /usr/local/sbin/logrotate /usr/local/etc/logrotate.d/vulture.conf
/home/vlt-gui/vulture/crontab/vlt-sys/dump_mongodb_vulture.hour
" > /home/vlt-sys/hour.sh

/bin/echo "[*] MongoDB tools successfully installed"

/bin/mkdir -p /var/db/mongodb_dumps
/bin/chmod 750 /var/db/mongodb_dumps
/usr/sbin/chown vlt-sys:vlt-sys /var/db/mongodb_dumps
