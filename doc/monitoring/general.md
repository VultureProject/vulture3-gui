---
title: "Monitoring"
currentMenu: healthcheck
parentMenu: getting-started
---

## "Status" menu

In this section you will find statistics and usefull information about the health of your Vulture cluster. It is important to check on a regularly basis that everything is working well. Vulture will retain 30 days of statistics within its internal database. Metrics are refreshed every minute by a Vulture internal crontab running as 'vlt-gui'. <br/>
Metrics are stored inside MongoDB repository. <br/>

### Status / General

On this view you will find the status of Vulture's main processes:
- `mongod`: The internal Vulture Database: Mandatory, must always be running.
- `haproxy`: The process in charge of load-balancing incoming trafic.
- `rsyslogd`: The process in charge of sending logs to remote syslog, mongodb or elastic.
- `pf`: The network Firewall, recommended, should always be running.
- `ntpd`: NTP daemon, should always run (it is mandatory that all Vulture nodes within a cluster are perfectly synchronized).
- `sshd`: Can be turned off to avoid SSH access over network.
- `redis`: Mandatory, must always be running.

You will also find:
 - The number of active Listeners (Number of IP addresses/ports on with Apache processes are listening)
 - The number of active Applications (Web Applications available through Vulture)

**Note that all these metrics are refreshed every minute**. The last system status' date and time is displayed on this page, so that you can check when the last probe has been done.<br/>
<br/>
Metrics are also available for Redis entries :
 - `OAuth2 Tokens`: Number of active OAuth2 tokens in Vulture's cache.
 - `Password Tokens`: Number of active password reset links sent.
 - `Temporary Tokens`: Number of temporary sessions (related to users redirected to the portal but not yet authentified).
 - `Portal Tokens`: Number of active portal sessions.
 - `Application Tokens`: Number of currently logged users on all application. A 30-days picture is available in the "Status / User" view (see below).
 - `UA Entries`: Number of User-Agent md5 hashes in redis.
 - `Reputation`: Indicates if the reputation database is loaded in redis.
 <br/>

At least, CPU / RAM and SWAP usage are displayed in real time (refreshed every second).

### Status / System

CPU, RAM, SWAP and partitions usage evolution are displayed on this page. You will also find the evolution of the number of processes running on each Vulture Node.

### Status / Network

##### `Bytes received over time`
This metric is collected with **psutil.net_io_counters / bytes_recv:** (https://pypi.python.org/pypi/psutil). <br/>
It is the number of bytes per second received by Vulture on all network interfaces.
<br/>
##### `Bytes sent over time`
This metric is collected with **psutil.net_io_counters / bytes_sent:** (https://pypi.python.org/pypi/psutil). <br/>
It is the number of bytes per second sent by Vulture on all network interfaces.
<br/>
##### `Number of entries in the firewall state table`
This metric is collected with **pfctl -si**. <br/>
This is a very important stat: It shows the number of active entries in the pf firewall state table. By default Vulture pf configuration allow 50,000 active entries in the pf state table. If you reach this limit, Vulture will refuse any new incoming connection. As a result, it won't be accessible anymore until some entries are removed from the state table. <br/>
You can increase this limit in the network firewall configuration (See [Network firewall](/doc/waf/pf.html)).
<br/>
##### `Incoming packet dropped`
This metric is collected with **psutil.net_io_counters / dropin** (https://pypi.python.org/pypi/psutil). <br/>
It is the total number of incoming packets which were dropped on all network interfaces.
<br/>
##### `Number of errors while receiving`
This metric is collected with **psutil.net_io_counters / errin ** (https://pypi.python.org/pypi/psutil). <br/>
It is the total number of errors while receiving.
<br/>
##### `Number of errors while sending`
This metric is collected with **psutil.net_io_counters / errout ** (https://pypi.python.org/pypi/psutil). <br/>
It is the total number of errors while sending.

### Status / Users

##### `Number of user sessions`
This metric is the evolution of the number of users logged on Vulture's application over time.

##### `Bytes received over time`
This metric is collected with **psutil.net_io_counters / bytes_recv:** (https://pypi.python.org/pypi/psutil). <br/>
It is the number of bytes per second received by Vulture on all network interfaces.
<br/>

## REST APIs

You can request some Vulture metrics through REST APIs. Vulture REST APIs are available on TCP port 8000, but you need a client certificate to make a request. Such a certifiate needs to be issued from the Vulture's internal PKI <br/>.
Here are some entry points :<br/>

** Is my Vulture node available ? **
```
curl --ssl -k -E <client_certificate.pem> https://my_node:8000/api/cluster/node/status/
{
    "status": true
}
```
** What are the current running versions of my Vulture node ? **
```
curl --ssl -k -E <client_certificate.pem> https://my_node:8000/api/cluster/node/version/
 {
    "gui-version": "GUI-1.2",
    "engine-version": "Engine-2.4.23-15"
 }
```

** What are the statuses of processes running on my node ? **
```
curl --ssl -k -E <client_certificate.pem> https://my_node:8000/api/supervision/process/
{
    "ntpd": "UP",
    "sshd": "UP",
    "haproxy": "UP",
    "rsyslogd": "UP",
    "mongod": "UP",
    "redis": "UP",
    "pf": "UP",
    "fail2ban": "DOWN",
    "Applications": "11/11",
    "Listeners": "3/3",
    "App. Sessions": 1428,
    "Portal Sessions": 22,
    "OAuth2 Sessions": 21,
    "Password Reset": 0,
    "Token": 5
}
```
