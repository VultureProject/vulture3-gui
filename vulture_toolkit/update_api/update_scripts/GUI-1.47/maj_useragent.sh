#!/bin/sh
#
# This migration script install ua-parser needed ressources
#
#

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/bin/echo "[*] Installing user-agent parser"

if [ ! -d "/var/db/useragent" ]; then
    /bin/mkdir /var/db/useragent/
    /usr/sbin/chown -R vlt-gui:vlt-web /var/db/useragent
    /bin/chmod 750 /var/db/useragent
fi

/usr/local/bin/wget --no-check-certificate https://raw.githubusercontent.com/ua-parser/uap-core/master/regexes.yaml -O /var/db/useragent/regexes.yaml >>/tmp/installation.log 2>&1
/usr/sbin/chown vlt-gui:vlt-web /var/db/useragent/regexes.yaml
/bin/chmod 644 /var/db/useragent/regexes.yaml

/bin/echo "[*] Install of user-agent parser successfully ended"
