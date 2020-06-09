#!/bin/sh
#
# This script updates gui and portal httpd.conf
#
#

/bin/echo -n "[+] Updating gui-httpd.conf ..."
cp /home/vlt-gui/vulture/vulture_toolkit/templates/gui_httpd.conf /home/vlt-sys/Engine/conf/gui-httpd.conf
/bin/echo -n "[+] Updating portal-httpd.conf ..."
cp /home/vlt-gui/vulture/vulture_toolkit/templates/portal_httpd.conf /home/vlt-sys/Engine/conf/portal-httpd.conf
/bin/echo "DONE"
