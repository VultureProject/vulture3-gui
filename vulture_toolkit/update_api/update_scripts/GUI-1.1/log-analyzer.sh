#!/bin/sh
#
# This migration script install log-analyzer service
#
#

echo '#!/bin/sh

# $FreeBSD$
#
# PROVIDE: loganalyzer
# REQUIRE: LOGIN
# KEYWORD: shutdown

# add the following line to /etc/rc.conf to enable the loganalyzer:
# loganalyzer_enable="YES"

. /etc/rc.subr

name="loganalyzer"
rcvar=`set_rcvar`

# default values
: ${loganalyzer_enable="YES"}

loganalyser_user=vlt-gui
base_path="/home/vlt-gui/vulture/vulture_toolkit/log/log-analyzer"
config_path="/usr/local/etc/loganalyzer.json"
pidfile="/var/run/loganalyzer.pid"

command="${base_path}/log-analyzer.py"
command_interpreter="/home/vlt-gui/env/bin/python2.7"
start_cmd="/usr/sbin/daemon -u vlt-gui -f -p $pidfile $command daemon -f $config_path"

load_rc_config $name
run_rc_command "$1"

' > /usr/local/etc/rc.d/loganalyzer

chmod +x /usr/local/etc/rc.d/loganalyzer

echo '
loganalyzer_enable="YES"
' >> /etc/rc.conf

service loganalyzer start