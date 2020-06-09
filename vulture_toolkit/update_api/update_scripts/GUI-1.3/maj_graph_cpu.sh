#!/bin/sh
#
# This script set a correct CPU graph in GUI
#

if [ $(/usr/bin/whoami) = "root" ]
then
    echo "#!/bin/sh

#IN=\`sysctl kern.cp_time | awk '{ print \$2\":\"\$3\":\"\$4\":\"\$5\":\"\$6 }'\`
IN=\`iostat -t proc 1 2 | tail -1f | awk '{ print \$3\":\"\$4\":\"\$5\":\"\$6\":\"\$7 }'\`
rrdtool update /var/db/rrdtools/cpu.rrd N:\$IN" > /home/vlt-sys/crontab/rrd-stats-minute/updates/update_cpu_rrd.minute
fi