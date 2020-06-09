#!/bin/sh
#
# This script downloads Geocities databases
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/bin/echo "[+] Downloading Geo Cities..."

#!/bin/sh
cd /var/db/loganalyzer/

/usr/local/bin/wget -q --no-check-certificate http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz
gunzip -f GeoLite2-City.mmdb.gz
chown vlt-gui:vlt-gui GeoLite2-City.mmdb




