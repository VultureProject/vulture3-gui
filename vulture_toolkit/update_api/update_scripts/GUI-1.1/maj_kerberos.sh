#!/bin/sh
#
#   This migration script update Vulture ( Kerberos module )
#
##############################################################

. /etc/rc.conf


/bin/echo -n "[+] Creating needed files..."
# Fill the configuration kerberos file with a sample
/bin/echo '[libdefaults]
	default_realm = ATHENA.MIT.EDU

[realms]
# use "kdc = ..." if realm admins havent put SRV records into DNS
	ATHENA.MIT.EDU = {
		admin_server = kerberos.mit.edu
	}
	ANDREW.CMU.EDU = {
		admin_server = kdc-01.andrew.cmu.edu
	}

[domain_realm]
	mit.edu = ATHENA.MIT.EDU
	csail.mit.edu = CSAIL.MIT.EDU
	.ucsc.edu = CATS.UCSC.EDU

[logging]
#	kdc = CONSOLE' > /etc/krb5.conf
/bin/chmod 640 /etc/krb5.conf
/usr/sbin/chown root:vlt-web /etc/krb5.conf

/usr/bin/touch /etc/krb5.keytab
/bin/chmod 640 /etc/krb5.keytab
/usr/sbin/chown root:vlt-portal /etc/krb5.keytab
/bin/echo "OK"

/bin/echo "[+] Uninstalling Kerberos pachage by pip"
/usr/bin/yes | /home/vlt-gui/env/bin/pip uninstall kerberos

/bin/echo "[+] Installing Kerberos packages via pkg"
if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi
env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg install --yes py27-kerberos


if [ $? -ne 0 ]
then
    /bin/echo "[/] It seems to have error while installing py27-kerberos package. Quitting."
    exit 1
fi

/bin/echo -n "[+] Linking library paths..."
if [ -f /usr/local/lib/python2.7/site-packages/kerberos.so ]
then
    /bin/ln -s /usr/local/lib/python2.7/site-packages/kerberos.so /home/vlt-gui/env/lib/python2.7/site-packages/kerberos.so
else
    /bin/echo "[/] It seems to have error while installing py27-kerberos package by PKG. Quitting."
    exit 1
fi
if [ -d /usr/local/lib/python2.7/site-packages/kerberos-1.1.1-py2.7.egg-info ]
then
    /bin/ln -s /usr/local/lib/python2.7/site-packages/kerberos-1.1.1-py2.7.egg-info /home/vlt-gui/env/lib/python2.7/site-packages/kerberos-1.1.1-py2.7.egg-info
else
    /bin/echo "[/] It seems to have error while installing py27-kerberos package by PKG. Quitting."
    exit 1
fi
/bin/echo "OK"

/bin/echo -n "[+] Creating necessary scripts..."
/bin/echo '#!/bin/sh

/bin/echo "Copying keytab in master keytab /etc/krb5.keytab"

# arguments:
# $1 : keytab_file to import

# Authorized files separated by a space
authorized_files="/tmp/tmp_keytab "

if [ $(/usr/bin/whoami) = "root" ]
then
    if [ ! -f /etc/krb5.keytab ]
    then
        /bin/echo "/etc/krb5.keytab does not exists. Creating it."
        /usr/bin/touch /etc/krb5.keytab
    fi
    # Verifying if the requested keytab is authorized
    authorized=0
    for file in $authorized_files
    do
        if [ "$file" = "$1" ]
        then
            authorized=1
        fi
    done
    if [ $authorized -eq 0 ]
    then
        /bin/echo "The requested keytab is not authorized to be imported."
    else
        /usr/sbin/ktutil copy $1 /etc/krb5.keytab
        # Delete tmp_keytab
        /bin/rm $1

        # Set permissions of keytab
        /usr/sbin/chown root:vlt-web /etc/krb5.keytab
        /bin/chmod 0640 /etc/krb5.keytab
    fi
else
    /bin/echo "You are not authorized to execute that file : only root can."
fi' > /home/vlt-sys/scripts/copy_keytab.sh

if [ $(/bin/ls /home/vlt-sys/scripts/* | /usr/bin/grep "get_tgt") == ""]
then
    /bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import print_function

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
__doc__ = ''
import sys
import kerberos
import os

nb_args = len(sys.argv)
if nb_args == 3:
    file_name = sys.argv[1]
    service_name = sys.argv[2]
    if file_name.startswith(\"/tmp/krb5cc_\") and len(file_name) == 52 :
        os.environ[\"KRB5CCNAME\"] = \"FILE:\"+file_name
        try:
            ignore, ctx = kerberos.authGSSClientInit(service_name)
            ignore = kerberos.authGSSClientStep(ctx,'')
            tgt = kerberos.authGSSClientResponse(ctx)
        except Exception, e:
            print(\"KERBEROS: Error while retrieving ticket for service {} : {}\".format(service_name,str(e)), file=sys.stderr)
            sys.exit(2)
        print(\"TGT=\"+tgt)
    else:
        print(\"NOT ALLOWED\", file=sys.stderr)
        sys.exit(2)
else:
    print(\"ARGS ERROR\", file=sys.stderr)
    sys.exit(2)
" > /home/vlt-sys/scripts/get_tgt
fi

/usr/sbin/chown root:wheel /home/vlt-sys/scripts/get_tgt
/bin/chmod 555 /home/vlt-sys/scripts/get_tgt
/bin/echo "OK"

/usr/sbin/chown root:wheel /home/vlt-sys/scripts/copy_keytab.sh
/bin/chmod 555 /home/vlt-sys/scripts/copy_keytab.sh

/bin/echo '#!/bin/sh

/bin/echo "Flushing /etc/krb5.keytab keytab..."

# arguments:
# None

if [ $(/usr/bin/whoami) = "root" ]
then
    /bin/cat /dev/null > /etc/krb5.keytab
else
    /bin/echo "You are not authorized to execute that file : only root can."
fi' > /home/vlt-sys/scripts/flush_keytab.sh

/usr/sbin/chown root:wheel /home/vlt-sys/scripts/flush_keytab.sh
/bin/chmod 555 /home/vlt-sys/scripts/flush_keytab.sh

if [ "$(cat /usr/local/etc/sudoers.d/vulture_sudoers | grep "vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/flush_keytab.sh")" != "" ]
then
    /bin/echo "This script has already been executed."
else
    /bin/echo 'vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/flush_keytab.sh' >> /usr/local/etc/sudoers.d/vulture_sudoers
fi
if [ "$(cat /usr/local/etc/sudoers.d/vulture_sudoers | grep "vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/copy_keytab.sh")" != "" ]
then
    /bin/echo "This script has already been executed."
else
    /bin/echo 'vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/copy_keytab.sh' >> /usr/local/etc/sudoers.d/vulture_sudoers
fi
if [ "$(cat /usr/local/etc/sudoers.d/vulture_sudoers | grep "vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/get_tgt")" != "" ]
then
    /bin/echo "This script has already been executed."
else
    /bin/echo 'vlt-sys ALL=NOPASSWD:/home/vlt-sys/scripts/get_tgt' >> /usr/local/etc/sudoers.d/vulture_sudoers
fi
if [ "$(cat /usr/local/etc/sudoers.d/vulture_sudoers | grep "vlt-portal ALL=(vlt-sys) NOPASSWD:/usr/local/bin/sudo")" != "" ]
then
    /bin/echo "This script has already been executed."
else
    /bin/echo 'vlt-portal ALL=(vlt-sys) NOPASSWD:/usr/local/bin/sudo' >> /usr/local/etc/sudoers.d/vulture_sudoers
fi

/bin/echo "#!/usr/bin/env /home/vlt-gui/env/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import print_function

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
__author__ = \"Florian Hagniel\"
__credits__ = []
__license__ = \"GPLv3\"
__version__ = \"3.0.0\"
__maintainer__ = \"Vulture Project\"
__email__ = \"contact@vultureproject.org\"
__doc__ = ''
import sys

nb_args = len(sys.argv)
if nb_args == 3:
    filename = sys.argv[1]
    content = sys.argv[2]
    allowed_files = ('/etc/resolv.conf',
                     '/etc/ntp.conf',
                     '/etc/mail/mailer.conf',
                     '/usr/local/etc/ssmtp/ssmtp.conf',
                     '/usr/local/etc/fluentd/fluent.conf',
                     '/usr/local/etc/redis.conf',
                     '/usr/local/etc/pf.conf',
                     '/usr/local/etc/sentinel.conf',
                     '/etc/rc.conf.local',
                     '/etc/krb5.conf',
                     '/usr/local/etc/rsyslog.d/rsyslog.conf',
                     '/usr/local/etc/loganalyzer.json',
                     '/home/vlt-sys/Engine/conf/gui-httpd.conf',
                     '/home/vlt-sys/Engine/conf/portal-httpd.conf',
    )
    # Testing IP Address validity
    if filename in allowed_files:
        f = open(filename, 'w')
        f.write(content)
        f.close()
    else:
        print(\"NOT ALLOWED\", file=sys.stderr)
        sys.exit(2)
else:
    print( \"ARGS ERROR\", file=sys.stderr)
    sys.exit(2)
" > /home/vlt-sys/scripts/write_configuration_file
echo "DONE"

# Add vlt-portal in "daemon" group
if [ $(/bin/cat /etc/group | /usr/bin/grep "daemon" | /usr/bin/grep "vlt-web") == ""]
then
    /usr/sbin/pw usermod vlt-portal -G vlt-web,daemon
fi


