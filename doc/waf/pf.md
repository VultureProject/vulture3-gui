---
title: "Packet Filter"
currentMenu: pf
parentMenu: waf
---

This interface gives you the ability to fine tune the packet filter configuration.<br/>

## General
### Firewall settings
`Configure Firewall Settings of`: The vulture node that you want to configure.<br/>
`Repository type`: Select whether a file or a data repository.<br/>
`Optional syslog repository`: Select a syslog repository that will log pf events.<br/>

### Firewall Status
The summary of pf status, whether it is currently running or not.<br/>
You can also reload the service, which is mandatory after each configuration change.<br/>

## Configuration
You can add pf rules here.<br/>
You have the possibility to tune<br/>
`Policy`: The action of the rule: Block / Pass<br/>
`Direction`: The direction of the rule: Inbound / Outbound / Both<br/>
`Log`: Toggle to log the event<br/>
`Inet`: IP <br/>
`Protocol`: TCP / UDP / ICMP (Ping) / All<br/>
`Source`: The source IP<br/>
`Destination`: The destination IP<br/>
`Port`: The targeted port<br/>
`Comment`: The rule comment<br/>
`Action`: Duplicate or delete the current rule<br/>

## Blacklist
### Permanent blacklist

Here you can enter one IP address or network range per line. <br/>
These addresses will be added to the `abusive_hosts` pf table. <br/><br/>
All connexion coming from any IP of this table will be dropped. Starting at GUI-1.41, the limit was set to 3 connexions per second. Since GUI-1.42 the limit was raised to 100 connexion per second<br/>
<br/>
Here is a pf cheat sheet to manage this blacklist table:

**Show blacklisted IPs**: `pfctl -t abusive_hosts -T show`

**Blacklist the IP '1.2.3.4'**: `pfctl -t abusive_hosts -T add 1.2.3.4`

**Remove the IP '1.2.3.4' from blacklist**: `pfctl -t abusive_hosts -T delete 1.2.3.4`


** If you have a firewall that perform address translation before Vulture, you must disable this feature in pf policy: **
```
Default:                pass log quick inet proto tcp from any to em0 port { 80, 443 } flags S/SA keep state (max-src-conn 100, max-src-conn-rate 100/1, overload <abusive_hosts> flush global)
Need to be changed to:  pass log quick inet proto tcp from any to em0 port { 80, 443 } flags S/SA keep state
```


## SSH Protection
Packet Filter is configured to protect against Brute Force attack on SSH. In case of 3 connections in less than 5 seconds, the IP address is blacklisted. <br/>
These addresses will be added to the previous `abusive_hosts` pf table. <br/><br/>

### Current active blacklist
Here you will see the result of the following command: `pfctl -t abusive_hosts -T show`

## Advanced configuration
### Rules
Raw pf configuration
