#!/bin/sh
#
# This migration script install authy, pillow and captcha
#
#

. /etc/rc.conf

/bin/echo "[+] Installing authentication modules authy, pillow and captcha ..."

if [ $(/usr/bin/whoami) = "root" ]
then
    if [ "$http_proxy" != "" ]
    then
        export https_proxy="http://$http_proxy"
        export http_proxy="http://$http_proxy"
    fi
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install jpeg
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install tiff
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install webp
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install lcms2
    /usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install freetype2
    echo $http_proxy
    env
    /home/vlt-gui/env/bin/pip install pillow
    /home/vlt-gui/env/bin/pip install authy
    /home/vlt-gui/env/bin/pip install captcha

    /bin/echo "[*] Installation ended successfully."
else
    /bin/echo "[/] You are not authorized to execute that file : only root can."
fi
