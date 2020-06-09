---
title: "Hardening guide"
currentMenu: security
parentMenu: installation
---

## Overview


Here you will find details on security measures inside Vulture.<br/>
We tried to find the good balance between security and usability inside Vulture. **If you find any security related problem within Vulture, please contact us at support@vultureproject.org**<br/>

## System

### System settings

These settings differs from default FreeBSD 11.0 installation. <br/>
/etc/sysctl.conf:
```
kern.ipc.maxsockbuf=16777216
kern.ipc.soacceptqueue=2048
kern.maxfilesperproc=117261
kern.maxprocperuid=64000
```

### Default accounts

The following accounts are created during Vulture's bootstrap:
```
/usr/sbin/pw useradd -n vlt-gui -s /bin/csh -m -w random
/usr/sbin/pw useradd -n vlt-portal -s /bin/csh -w random
/usr/sbin/pw useradd -n vlt-sys -s /bin/csh -m -w random
/usr/sbin/pw useradd -n vlt-data -s /bin/csh -w random
/usr/sbin/pw useradd -n vlt-adm -s /bin/csh -m -w none
/usr/sbin/pw useradd -n haproxy -s /usr/sbin/nologin -m -w random
```

As you can see, vlt-gui, vlt-portal, vlt-sys and vlt-data have random password. This means one may be able to connect to Vulture through an ssh brute-force attack on this account. <br/>
You may want to enforce security by locking these accounts, with `pw lock vlt-gui` for example.

`haproxy` account cannot log in onto the system.

`vlt-adm` is the administrative account of Vulture and should have a robust password.
This password is scrambled during bootstrap.

**Note:** When you install Vulture choose a robust root password

### OpenSSH

OpenSSH is enabled by default. You can disable it [from the GUI](/doc/management/services.html) and enable it when needed.

## Network

### System settings

These settings differs from default FreeBSD 11.0 installation. <br/>
/etc/sysctl.conf:
```
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
```

### Packet filter

PF is an important security part of Vulture. The default filtering policy is shown below.

`You need to adapt this policy to your needs and whenever you add new listeners in Vulture.
In particular, be sure to never allow inter-cluster ports from outside. THIS IS ENABLE BY DEFAULT!`


```
#These limits are far beyond FreeBSD's pf default limit.
set limit { states 100000, frags 25000, src-nodes 50000 }

pass quick on lo0 all

#The default Vulture's pf policy is:
# - Drop and log everything in input
# - Accept any outgoing traffic
# - IPV6 is enabled by default

block in log all
pass in proto icmp6 all
pass out proto icmp6 all
pass out all keep state

# Whitelist for Vulture Cluster
# This table is auto managed by Vulture
table <vulture_cluster> persist file "/usr/local/etc/pf.vulturecluster.conf"
pass in quick from <vulture_cluster>

# Brute force / SYN Flood / DDOS mitigation rule
# Use pfctl -t abusive_hosts -T show to show currently blacklisted hosts
# You can add manual persistent IP in this file
table <abusive_hosts> persist file "/usr/local/etc/pf.abuse.conf"
block in log quick from <abusive_hosts>

# Incoming policy: By default, HTTP and HTTPS ports are accepted from everywhere on em0
pass log quick inet proto tcp from any to em0 port { 80, 443 } flags S/SA keep state \
                                (max-src-conn 100, max-src-conn-rate 15/5, \
                                 overload <abusive_hosts> flush global)

# SSH brute-force protection
# Incoming policy: By default, SSH port is accepted from everywhere
pass log quick inet proto tcp from any to em0 port 22 flags S/SA keep state \
                                (max-src-conn 100, max-src-conn-rate 3/5, \
                                 overload <ssh_abusive_hosts> flush global)


# Incoming policy: By default inter-cluster communication are allowed from everywhere on em0
pass quick proto tcp from any to em0 port 8000 flags S/SA keep state
pass quick proto tcp from any to em0 port { 6379, 9091, 26379 } flags S/SA keep state

# ---- Allow CARP communications between nodes
pass in proto carp all
```
`
