#!/bin/sh
#
# This script install libmaxminddb
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/bin/echo "[+] Installing libmaxminddb..."

if [ $(/usr/bin/whoami) = "root" ]; then
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install libmaxminddb
fi

cd /var/db/loganalyzer/
rm -f GeoLiteCity.dat
rm -f GeoLite2-Country.mmdb.gz
/usr/local/bin/wget -q --no-check-certificate http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.mmdb.gz
gunzip -f GeoLite2-Country.mmdb.gz
chown vlt-gui:daemon GeoLite2-Country.mmdb

echo "#!/bin/sh
cd /var/db/loganalyzer/
/usr/local/bin/wget -q --no-check-certificate http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.mmdb.gz
gunzip -f GeoLite2-Country.mmdb.gz
chown vlt-gui:daemon GeoLite2-Country.mmdb
" > /home/vlt-gui/vulture/crontab/vlt-gui/geolite.day
chown vlt-gui:vlt-gui /home/vlt-gui/vulture/crontab/vlt-gui/geolite.day
chmod 750 /home/vlt-gui/vulture/crontab/vlt-gui/geolite.day





