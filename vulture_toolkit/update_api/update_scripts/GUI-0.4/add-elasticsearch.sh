#!/bin/sh
#
# This migration script install elasticsearch
#
#
. /etc/rc.conf

proxy=""
if [ "$http_proxy" != "" ]
then
    /home/vlt-gui/env/bin/pip2.7 --proxy="http://$http_proxy" install elasticsearch
else
    /home/vlt-gui/env/bin/pip2.7 install elasticsearch
fi