#!/bin/sh
#
# This migration script re-link system kerberos lib to virtual env
#
#

/bin/echo -n "[+] Re-linking kerberos lib ..."
/bin/ln -s /usr/local/lib/python2.7/site-packages/kerberos* /home/vlt-gui/env/lib/python2.7/site-packages
/bin/echo "OK"
