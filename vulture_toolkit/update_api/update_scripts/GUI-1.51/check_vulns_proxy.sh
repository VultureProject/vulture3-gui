#!/bin/sh
#
# Script Name: check_vulns_proxy
#
# Author: Kevin Guillemot
# Date : 21/02/2018
#
# Description: This migration script update the /home/vlt-sys/scripts/get_vulns script
#                to handle proxy configuration
#
# Run Information: This script is run automatically by Vulture updater process
#


vulns_script="/home/vlt-sys/scripts/get_vulns"

/bin/echo -n "[+] Updating $vulns_script script ..."

/bin/echo "#!/bin/sh

# arguments:
# \$1 : type of vulnerabilities to check
# \$2 : Verbosity (\"True\" or \"False\")

. /etc/rc.conf

# export proxy for pkg
if [ \"\$http_proxy\" != \"\" ]
then
    export https_proxy=\"http://\$http_proxy\"
    export http_proxy=\"http://\$http_proxy\"
fi

if [ \$(/usr/bin/whoami) = \"root\" ]
then
    options=\"-F\"
    if [ \"\$2\" = \"False\" ]
    then
        options=\"\$options -q\"
    elif [ \"\$2\" != \"True\" ]
    then
        /bin/echo \"Second argument(verbosity) not recognized, choices are 'True' or 'False'\"
        exit
    fi
    if [ \"\$1\" = \"global\" ]
    then
        /usr/sbin/pkg audit \$options
    elif [ \"\$1\" = \"kernel\" ]
    then
	    /usr/sbin/pkg audit \$options \$(freebsd-version -k | /usr/bin/sed 's,^,FreeBSD-kernel-,;s,-RELEASE-p,_,;s,-RELEASE\$,,')
    elif [ \"\$1\" = \"distrib\" ]
    then
	    /usr/sbin/pkg audit \$options \$(freebsd-version -u | /usr/bin/sed 's,^,FreeBSD-,;s,-RELEASE-p,_,;s,-RELEASE\$,,')
    else
        /bin/echo \"Argument not recognized, choices are : 'global','distrib' or 'kernel'\"
    fi
else
    /bin/echo \"You are not authorized to execute that file : only root can.\"
fi
" > "$vulns_script"
/bin/echo "OK"

/bin/echo -n "[+] Setting permissions ..."
/bin/chmod 550 "$vulns_script"
/usr/sbin/chown vlt-sys:vlt-sys "$vulns_script"
/bin/echo "OK"

/bin/echo -n "[+] Executing check_vulns crontab hourly script ..."
/usr/bin/su -m vlt-gui -c /home/vlt-gui/vulture/crontab/vlt-gui/check_vulns.hour
/bin/echo "OK"

