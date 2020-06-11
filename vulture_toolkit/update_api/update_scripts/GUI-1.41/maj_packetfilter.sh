#!/bin/sh
#
# This script install crontab for pf logs
#
#
/bin/echo '#!/bin/sh

PFLOG=/var/log/pflog
FILE=/var/log/pflog1min.$(date "+%Y%m%d%H%M")
/usr/local/bin/sudo /usr/bin/pkill -ALRM -u root -U root -t - -x pflogd
sleep 1 
if [ $(/usr/bin/stat -f %z $PFLOG) -gt 24 ]; then
   /usr/local/bin/sudo mv $PFLOG $FILE
   /usr/local/bin/sudo /usr/bin/pkill -HUP -u root -U root -t - -x pflogd
   /usr/local/bin/sudo /usr/sbin/tcpdump -n -e -s 160 -ttt -r $FILE | /usr/bin/logger -t pf -p local0.info
   /usr/local/bin/sudo rm $FILE
fi' > /home/vlt-sys/crontab/pflog.sh


/usr/bin/touch /var/log/pflog.log
/bin/chmod +x /home/vlt-sys/crontab/pflog.sh

/usr/bin/touch /usr/local/etc/pf.conf
/usr/sbin/chown root:wheel /usr/local/etc/pf.conf

/bin/echo "/usr/local/bin/sudo /home/vlt-gui/vulture/crontab/vlt-sys/pflog.sh >/dev/null 2>&1" > /home/vlt-sys/minute.sh

## Add to sudoers
/bin/echo "vlt-sys ALL=NOPASSWD:/home/vlt-sys/crontab/pflog.sh" >> /usr/local/etc/sudoers.d/vulture_sudoers



val=`/bin/cat /etc/rc.conf | /usr/bin/grep 'pf_enable="YES"'`
if [ "$val" == "" ]
then
	/bin/echo '
pf_enable="YES"

# PF Rules File
pf_rules="/usr/local/etc/pf.conf"' >> /etc/rc.conf
fi

kldload pf 2> /dev/null
/sbin/pfctl -e 2> /dev/null