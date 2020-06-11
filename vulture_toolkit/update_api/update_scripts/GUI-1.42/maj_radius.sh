#!/bin/sh
#
# This script update bad file radius dictionnary and reinstall pyrad and apply patches
#
#
. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/home/vlt-gui/env/bin/pip install --force-reinstall -I pyrad

/usr/bin/patch -p0 -s < /home/vlt-gui/vulture/vulture_toolkit/update_api/update_scripts/GUI-1.42/dictionary.patch

/usr/bin/sed -i '' 's/3GPP-RAT-TYPE/3GPP-RAT-Type/' /usr/local/share/dictionaries/dictionary.3gpp
