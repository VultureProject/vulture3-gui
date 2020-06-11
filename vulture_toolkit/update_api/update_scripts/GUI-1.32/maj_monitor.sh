#!/bin/sh

. /etc/rc.conf

if [ "$http_proxy" != "" ]
then
    export https_proxy="http://$http_proxy"
    export http_proxy="http://$http_proxy"
fi

/usr/bin/touch /home/vlt-gui/crontab/monitor/monitor.minute
/bin/echo "#!/home/vlt-gui/env/bin/python

import sys, os, logging, datetime

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vulture.settings')

import django
django.setup()


from gui.models.monitor_settings import Monitor

m = Monitor()
m.add()" > /home/vlt-gui/crontab/monitor/monitor.minute

/usr/sbin/chown vlt-gui:vlt-gui /home/vlt-gui/crontab/monitor/monitor.minute
/bin/chmod 750 /home/vlt-gui/crontab/monitor/monitor.minute

/home/vlt-gui/env/bin/pip install psutil

## Removing rrdtool
/usr/bin/env ASSUME_ALWAYS_YES=YES /usr/sbin/pkg remove rrdtool
/bin/rm -r /home/vlt-sys/crontab/create-rrd
/bin/rm -r /home/vlt-sys/crontab/rrd-stats-minute

/bin/echo "#!/bin/sh 

" > /home/vlt-sys/minute.sh