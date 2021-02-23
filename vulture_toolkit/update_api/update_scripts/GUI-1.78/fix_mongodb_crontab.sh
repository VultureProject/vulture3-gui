#!/bin/sh
#
# This migration script install newest Vulture-LIBS package
#
#

. /etc/rc.conf

cat - << EOF > /etc/rc.conf.d/mongod
mongod_poststart()
{
    if [ -f \${pidfile} ]; then
        (chgrp vlt-sys \${pidfile} && chmod g+r \${pidfile})  || return 1
    fi
    return 0
}
start_postcmd="mongod_poststart"
EOF

echo "[+] Restarting Mongodb to take changes ..."
/usr/sbin/service mongod restart
echo "[*] Done"
