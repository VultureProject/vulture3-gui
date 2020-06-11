#!/bin/sh
#
# This script replace /usr/local/etc/sudoers.d/vulture_sudoers file
#
#

if [ "$(/bin/cat /usr/local/etc/sudoers.d/vulture_sudoers | /usr/bin/grep "vlt-sys ALL=NOPASSWD:/home/vlt-gui/vulture/crontab/vlt-sys/pflog.sh")" != "" ]
then
    /bin/echo "This script has already been executed."
else
    /bin/echo 'vlt-adm ALL=(ALL) ALL
vlt-adm ALL=NOPASSWD:/var/bootstrap/bootstrap.py
vlt-adm ALL=NOPASSWD:/usr/sbin/pw mod user vlt-adm -h 0
vlt-gui ALL=(vlt-sys) NOPASSWD:/usr/local/bin/sudo
vlt-portal ALL=(vlt-sys) NOPASSWD:/usr/local/bin/sudo
vlt-sys ALL=NOPASSWD:/usr/local/bin/sudo
vlt-sys ALL=NOPASSWD:/usr/sbin/service
vlt-sys ALL=NOPASSWD:/home/vlt-sys/Engine/bin/httpd
vlt-sys ALL=NOPASSWD:/sbin/ifconfig
vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/add_to_etc_hosts
vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/write_configuration_file
vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/get_content
vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/get_vulns
vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/install_updates
vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/check_updates.hour
vlt-sys ALL=NOPASSWD:/sbin/pfctl
vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/flush_keytab.sh
vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/copy_keytab.sh
vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/get_tgt
vlt-sys ALL=NOPASSWD:/usr/local/sbin/logrotate
vlt-sys ALL=NOPASSWD:/home/vlt-gui/vulture/crontab/vlt-sys/pflog.sh
' > /usr/local/etc/sudoers.d/vulture_sudoers
fi