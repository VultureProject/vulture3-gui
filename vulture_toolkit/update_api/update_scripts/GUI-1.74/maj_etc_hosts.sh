#!/bin/sh
#
# This migration script install newest Vulture-LIBS package
#
#

/bin/echo "[+] Updating file /etc/hosts..."

/usr/bin/sed -i '' '/dl.vultureproject.org/d' /etc/hosts

/bin/echo "[*] File /etc/hosts updated"
