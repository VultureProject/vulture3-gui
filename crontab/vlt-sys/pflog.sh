#!/bin/sh

#If we are already running, just exit
pgrep tcpdump 2> /dev/null > /dev/null
if [ "$?" == "0" ]; then
    exit
fi

echo "Collecting pflogs..."
host=`hostname`
tz=`date +%Z`
/usr/local/bin/sudo /usr/local/bin/sudo /bin/sh -c "/usr/sbin/tcpdump -l -n -e -s 160 -tttt -i pflog0 | sed -e \"s/\([0-9]*-[0-9]*-[0-9]*\) \([0-9]*:[0-9]*:[0-9]*\)\.[0-9]*/$host \1T\2:$tz/g\" | tee -a /var/log/pflog.log"

