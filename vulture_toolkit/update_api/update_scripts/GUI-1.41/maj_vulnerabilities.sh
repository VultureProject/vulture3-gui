#!/bin/sh
#
# Script to create and add required files and lines by the vulnerabilities checking fonctionality
#

/bin/echo "#!/bin/sh

# arguments:
# \$1 : type of vulnerabilities to check
# \$2 : Verbosity (\"True\" or \"False\")

. /etc/rc.conf
export http_proxy=\"\$http_proxy\"


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
        /usr/bin/env ASSUME_ALWAYS_YES=YES http_proxy=\$http_proxy /usr/sbin/pkg audit \$options
    elif [ \"\$1\" = \"kernel\" ]
    then
	    /usr/bin/env ASSUME_ALWAYS_YES=YES http_proxy=\$http_proxy /usr/sbin/pkg audit \$options \$(freebsd-version -k | /usr/bin/sed 's,^,FreeBSD-kernel-,;s,-RELEASE-p,_,;s,-RELEASE$,,')
    elif [ \"\$1\" = \"distrib\" ]
    then
	    /usr/bin/env ASSUME_ALWAYS_YES=YES http_proxy=\$http_proxy /usr/sbin/pkg audit \$options \$(freebsd-version -u | /usr/bin/sed 's,^,FreeBSD-,;s,-RELEASE-p,_,;s,-RELEASE$,,')
    else
        /bin/echo \"Argument not recognized, choices are : 'global','distrib' or 'kernel'\"
    fi
else
    /bin/echo \"You are not authorized to execute that file : only root can.\"
fi
" > /home/vlt-sys/scripts/get_vulns
/bin/chmod 750 /home/vlt-sys/scripts/get_vulns
/usr/sbin/chown vlt-sys:vlt-sys /home/vlt-sys/scripts/get_vulns
