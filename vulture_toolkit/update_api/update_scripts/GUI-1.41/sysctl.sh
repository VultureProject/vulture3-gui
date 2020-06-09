#!/bin/sh
#
# This migration script improve performance
#
#

echo "#Network Tuning - Sized for 10 GE networks
kern.ipc.maxsockbuf=16777216
kern.ipc.soacceptqueue=2048
kern.maxfilesperproc=117261
kern.maxprocperuid=64000

net.inet.tcp.sendbuf_max=16777216
net.inet.tcp.recvbuf_max=16777216
net.inet.tcp.sendbuf_auto=1
net.inet.tcp.recvbuf_auto=1
net.inet.tcp.sendbuf_inc=16384
net.inet.tcp.recvbuf_inc=524288

net.inet.tcp.mssdflt=1460
net.inet.tcp.minmss=1300
net.inet.tcp.syncache.rexmtlimit=0
net.inet.tcp.syncookies=0
net.inet.tcp.tso=0
net.inet.ip.check_interface=1
net.inet.ip.process_options=0
net.inet.ip.random_id=1
net.inet.ip.redirect=0
net.inet.icmp.drop_redirect=1
net.inet.tcp.always_keepalive=0
net.inet.tcp.drop_synfin=1
net.inet.tcp.ecn.enable=1
net.inet.tcp.icmp_may_rst=0
net.inet.tcp.msl=5000
net.inet.udp.blackhole=1
net.inet.tcp.blackhole=2
net.inet.carp.preempt=1
" > /etc/sysctl.conf

/sbin/sysctl -f /etc/sysctl.conf

