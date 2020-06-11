#!/bin/sh
#
# Script to create and add required files and lines by the vulnerabilities checking fonctionality
#

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python2.7
# -*- coding: utf-8 -*-
\"\"\"This file is part of Vulture 3.

Vulture 3 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Vulture 3 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vulture 3.  If not, see http://www.gnu.org/licenses/.
\"\"\"
__author__ = \"Kevin Guillemot\"
__credits__ = []
__license__ = \"GPLv3\"
__version__ = \"3.0.0\"
__maintainer__ = \"Vulture Project\"
__email__ = \"contact@vultureproject.org\"
__doc__ =  ''

import sys
import os

# Django setup part
sys.path.append(\"/home/vlt-gui/vulture/\")
os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", 'vulture.settings')

import django
django.setup()
import logging
logger = logging.getLogger('cluster')

#from vulture_toolkit.update_api.update_utils import UpdateUtils
from gui.models.system_settings import Cluster, Vulnerabilities

try:
    logger.info(\"Starting check vulns process\")
    cluster = Cluster.objects.get()
    node = cluster.get_current_node()
    node.vulns = Vulnerabilities()

    vulns = node.vulns.get_global_vulns()
    if vulns:
        logger.info(\"New global vulnerabilities : {}\".format(vulns))
        node.vulns.need_update = True
        node.vulns.global_vulns = vulns
        verbose_vuln = node.vulns.get_global_vulns(verbose=True) or \"\"
        try:
            verbose_vuln = \"<br>\".join([x for x in verbose_vuln.split('\n') if x != \"\"])
        except:
            pass
        node.vulns.global_vulns_verbose = verbose_vuln

    vulns = node.vulns.get_distrib_vulns()
    if vulns:
        logger.info(\"New FreeBSD vulnerabilities : {}\".format(vulns))
        node.vulns.need_update = True
        node.vulns.distrib_vulns = vulns
        verbose_vuln = node.vulns.get_distrib_vulns(verbose=True) or \"\"
        try:
            verbose_vuln = \"<br>\".join([x for x in verbose_vuln.split('\n') if x != \"\"])
        except:
            pass
        node.vulns.distrib_vulns_verbose = verbose_vuln

    vulns = node.vulns.get_kernel_vulns()
    if vulns:
        logger.info(\"New Kernel vulnerabilities : {}\".format(vulns))
        node.vulns.need_update = True
        node.vulns.kernel_vulns = vulns
        verbose_vuln = node.vulns.get_kernel_vulns(verbose=True) or \"\"
        try:
            verbose_vuln = \"<br>\".join([x for x in verbose_vuln.split('\n') if x != \"\"])
        except:
            pass
        node.vulns.kernel_vulns_verbose = verbose_vuln

    node.save()
    logger.info(\"Ending check vulns process\")
except Exception as e:
    logger.error(\"An error has occurred during check vulns process\")
    logger.exception(e)
" > /home/vlt-gui/crontab/monitor/check_vulns.hour
/bin/chmod 750 /home/vlt-gui/crontab/monitor/check_vulns.hour
/usr/sbin/chown vlt-gui:vlt-gui /home/vlt-gui/crontab/monitor/check_vulns.hour



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

if [ "$(cat /usr/local/etc/sudoers.d/vulture_sudoers | grep "vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/get_vulns")" != "" ] 
then
    /bin/echo "This script has already been executed."
else
    /bin/echo 'vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/get_vulns' >> /usr/local/etc/sudoers.d/vulture_sudoers
fi

/usr/bin/su -m vlt-gui -c /home/vlt-gui/crontab/monitor/check_vulns.hour
