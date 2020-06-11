#!/bin/sh

/bin/echo "#!/bin/sh
for each in /home/vlt-gui/crontab/monitor/*.minute ; do \$each ; done
/home/vlt-gui/env/bin/python /home/vlt-gui/vulture/testing/testing_client.py" > /home/vlt-gui/minute_gui.sh
