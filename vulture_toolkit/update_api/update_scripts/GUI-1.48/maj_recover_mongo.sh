#!/bin/sh
#
# This script creates recover mongo scripts
#
#

/bin/echo "[*] Mongo recover scripts..."

if [ ! -d "/home/vlt-sys/recover" ]; then
    /bin/mkdir /home/vlt-sys/recover
    /usr/sbin/chown -R vlt-sys:vlt-sys /home/vlt-sys/recover
    /bin/chmod 770 /home/vlt-sys/recover
fi

    /bin/echo "#!/bin/sh

mongod_status () {
    pidfile='/var/db/mongodb/mongod.lock'

    if ! [ -s \${pidfile} ]; then
        return 1
    fi

    pid=\`cat \${pidfile} 2>/dev/null || echo 0\`

    if [ \"\$pid\" -le 0 ]; then
        return 1
    fi

    ps aux | grep \${pid} | grep mongod 2>/dev/null >/dev/null
    if [ \"\$?\" -ne 0 ]; then
        return 1
    fi

    return 0
}
echo \"[*] WARNING: You're about to recover vulture's mongo primary database!\"
echo '[*] For more informations about the restore mongo procedure, please read https://www.vultureproject.org/doc/troubleshooting/troubleshooting.html.'
printf '[*] Are you sure you want to continue? [Y/N] '
read -r answer

if echo \"\$answer\" | grep -iq \"^[Yy]\$\" ;then
    . /etc/rc.conf

    if mongod_status; then
        echo \"[*] Recovery stopped, mongod service is running!\"
        exit 0
    fi

    rm -Rf /var/db/mongodb/WiredTiger* /var/db/mongodb/index* /var/db/mongodb/collection* /var/db/mongodb/_mdb_catalog.wt /var/db/mongodb/diagnostic.data/ /var/db/mongodb/journal/ /var/db/mongodb/mongo.lock /var/db/mongodb/sizeStorer.wt /var/db/mongodb/storage.bson
    service mongod start

    COUNTER=0
    echo '[*] Waiting for mongo to initialize...'
    while !(nc -z \$hostname 9091) && [ \"\$COUNTER\" -lt 60 ]; do
        sleep 2
        COUNTER=\$((\$COUNTER+2))
    done

    if [ \"\$COUNTER\" -gt 59 ]; then
        echo \"[*] Recovery stopped, mongo server server is not responding after \$COUNTER seconds!\"
        exit 1
    fi

    msg=\$(/usr/local/bin/mongo --quiet --eval 'rs.initiate()' --ssl --sslPEMKeyFile /var/db/mongodb/mongod.pem --sslCAFile /var/db/mongodb/ca.pem \$hostname:9091/vulture)
    ok=\$(echo \$msg | egrep -o 'ok\\\" : ([^,]+)' | cut -d ' ' -f 3)
    errmsg=\$(echo \$msg | egrep -o 'errmsg\\\" : ([^,]+)' | cut -d '\"' -f 3)

    if [ \"\$ok\" -eq 0 ]; then
        echo \"[!] rs.initiate() error: \$errmsg\"
        echo \"[!] Recovery failed.\"
        exit 1
    fi

    if [ -z \"\$1\" ]; then
        archive=\$(/bin/ls -t /var/db/mongodb_dumps/vulture_dump_*.archive | /usr/bin/head -1)
    else
        archive=\$1
    fi

    echo \"\$archive\"

    /usr/local/bin/mongorestore --gzip --db vulture --archive=\$archive --ssl --sslPEMKeyFile /var/db/mongodb/mongod.pem --sslCAFile /var/db/mongodb/ca.pem --host \$hostname --port 9091

    if [ \"\$?\" -ne 0 ]; then
        echo \"[!] mongorestore failed. Please check if the mongo dump used is correct (you can also pass a mongo dump archive as arg).\"
        exit 1
    fi

    echo \"[*] Mongo primary recovery done. If you have a Mongo ReplicatSet don't forget to execute recover_mongo_secondary.sh for each of your secondaries vulture nodes.\"
    exit 0
fi
" > /home/vlt-sys/recover/recover_mongo_primary.sh

/usr/sbin/chown -R vlt-sys:vlt-sys /home/vlt-sys/recover/recover_mongo_primary.sh
/bin/chmod 770 /home/vlt-sys/recover/recover_mongo_primary.sh



/bin/echo "#!/bin/sh

mongod_status () {
    pidfile='/var/db/mongodb/mongod.lock'

    if ! [ -s \${pidfile} ]; then
        return 1
    fi

    pid=\`cat \${pidfile} 2>/dev/null || echo 0\`

    if [ \"\$pid\" -le 0 ]; then
        return 1
    fi

    ps aux | grep \${pid} | grep mongod 2>/dev/null >/dev/null
    if [ \"\$?\" -ne 0 ]; then
        return 1
    fi

    return 0
}

echo \"[*] WARNING: You're about to recover vulture\'s mongo secondary database!\"
echo '[*] For more informations about the restore mongo procedure, please read https://www.vultureproject.org/doc/troubleshooting/troubleshooting.html.'
printf '[*] Are you sure you want to continue? [Y/N] '
read -r answer

if echo \"\$answer\" | grep -iq \"^[Yy]\$\" ;then
    . /etc/rc.conf

    if mongod_status; then
        echo \"[!] Recovey stopped, mongod service is running!\"
        exit 1
    fi
        rm -Rf /var/db/mongodb/WiredTiger* /var/db/mongodb/index* /var/db/mongodb/collection* /var/db/mongodb/_mdb_catalog.wt /var/db/mongodb/diagnostic.data/ /var/db/mongodb/journal/ /var/db/mongodb/mongo.lock /var/db/mongodb/sizeStorer.wt /var/db/mongodb/storage.bson
        service mongod start

        if [ \"\$?\" -ne 0 ]; then
            echo \"[!] Couldn't start mongod service.\"
            exit 1
        fi

        echo '[*] Done. mongod started.'
        echo '[*] Now you need to re-add this vulture node from the GUI in Management->Nodes to add this ReplicatSet as secondary.'
        echo '[*] More detailed instructions at https://www.vultureproject.org/doc/troubleshooting/troubleshooting.html.'
        exit 0
fi
" > /home/vlt-sys/recover/recover_mongo_secondary.sh

/usr/sbin/chown -R vlt-sys:vlt-sys /home/vlt-sys/recover/recover_mongo_secondary.sh
/bin/chmod 770 /home/vlt-sys/recover/recover_mongo_secondary.sh

/bin/echo "[*] Install of Mongo recover scripts successfully ended"
