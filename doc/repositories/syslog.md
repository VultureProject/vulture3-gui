---
title: "Syslog repository"
currentMenu: syslog
parentMenu: repositories
---

## Overview

Vulture supports syslog repositories. It can forwards logs to a remote syslog server. <br/>
The syslog forwarder is built on top of rsyslogd.<br/>
<br/>
Here is the information needed to create a syslog repository:<br/>


* `Repository name`: Friendly name for the syslog repo.
* `Syslog server IP Address`: IPv4 or IPv6 Ip address of your syslog server.
* `Syslog server port number`: TCP / UDP port to use.
* `Syslog protocol`: Network protocol (UDP or TCP).
* `Syslog keepalive`: For TCP protocal, you can configure the Keepalive to improve performances
* `Syslog facility`: The syslog facility used to send events.
* `Syslog security level`: Criticality level of the message (not used at the moment).

Once done, click on 'Test Syslog connection' to test the connection from Vulture to your syslog server.<br/>
During this test, Vulture will try to send "Vulture test \n" on the remote syslog server. <br/>
Check that you received it on server side.


You can customize rsyslog.conf (/home/vlt-gui/vulture/vulture_toolkit/templates/rsyslog.conf) template file and add / modify custom directives. <br/>
But in case of a Vulture upgrade, the file will be overwritten with the one provided in the new Vulture release.


## Activate your syslog repo

Once created, you can use this repo :
 - In the packet filter configuration, to forward packet filter logs. See [Packet Filter configuration](/doc/waf/pf.html)
 - In a log profile, to forward Apache logs. See [Logs profile](/doc/configuration/logs.html)

You can forward logs via syslog whatever the "initial" data repo is (File, MongoDB or Elastic).
