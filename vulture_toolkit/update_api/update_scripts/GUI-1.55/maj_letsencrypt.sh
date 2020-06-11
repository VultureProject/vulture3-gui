#!/bin/sh

/bin/echo "[+] Installing Let's encrypt package"

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install acme-client

conf_file="/etc/periodic.conf"
/bin/echo -n "Updating /etc/periodic.conf file ..."
/bin/echo 'weekly_acme_client_enable="YES"' > "$conf_file"
/bin/echo 'weekly_acme_client_challengedir="/home/vlt-sys/Engine/conf/acme-challenge"' >> "$conf_file"
/bin/echo 'weekly_acme_client_renewscript="/home/vlt-gui/vulture/crontab/vlt-gui/acme-renew.py"' >> "$conf_file"
/bin/echo "DONE"

src_path="/home/vlt-sys/Engine/acme-challenge"
dst_path="/home/vlt-sys/Engine/conf/acme-challenge"
/bin/echo -n "Moving $src_path to $dst_path ..."
if [ -d "$src_path" ]
then
    /bin/mv "$src_path" "$dst_path"
else
    /bin/echo "Creating directory $dst_path"
    /bin/mkdir "$dst_path"
fi
/bin/echo "Applying permissions to $dst_path"
/usr/sbin/chown vlt-sys:daemon "$dst_path"
/bin/chmod 750 "$dst_path"
/bin/echo "DONE"
