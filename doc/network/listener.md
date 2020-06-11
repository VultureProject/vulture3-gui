---
title: "Listeners"
currentMenu: listener
parentMenu: network
---

## Overview

You can manage listeners to add/remove IP addresses to Vulture nodes. Once created, you will be able to bind Vulture processes onto these IP Addresses. <br/>
There are several types of listeners: <br/>
 - `MAIN Listener`: This is the first, and main, IP address of the selected network interface (defined with "ifconfig em0 ...").
 - `ALIAS Listener`: This is an additional IP address on the selected network interface (defined with "ifconfig em0 ... alias0").
 - `CARP Listener`: This is a CARP listener.

<br/>
**Note**: Vulture's management IP is used for inter-cluster communication. <br/>
`You cannot change this IP address from the GUI.`


## Create a listener

Click on "Add an entry" to create a new listener. <br/>
Following options are available: <br/>
 - `Name`: A friendly name for the listener.
 - `Device`: The network device to use.
 - `IP Address`: The IP address to listen on.
 - `Netmask`: The associated netmask.
 - `Management Listener`: Do not use. This is not implemented, yet :-).

### CARP listener

As stated from https://www.freebsd.org/doc/handbook/carp.html:<br/><br/>
*The Common Address Redundancy Protocol (CARP) allows multiple hosts to share the same IP address and Virtual Host ID (VHID) in order to provide high availability for one or more services. This means that one or more hosts can fail, and the other hosts will transparently take over so that users do not see a service failure.
<br/><br/>In addition to the shared IP address, each host has its own IP address for management and configuration. All of the machines that share an IP address have the same VHID. The VHID for each virtual IP address must be unique across the broadcast domain of the network interface.
<br/><br/>High availability using CARP is built into FreeBSD, though the steps to configure it vary slightly depending upon the FreeBSD version. This section provides the same example configuration for versions before and equal to or after FreeBSD 10.
*


To create a CARP listener in a Vulture Cluster, additional parameters are required:
 - `VHID`: The Virtual Host ID for your CARP device.
 - `Devices for CARP Cluster`:
    - List here all the Vulture nodes / `network interface` you want to use. The CARP IP address will be shared between these nodes.
    - For each declared device, you will need to set `priority`. This is an integer, the lower = the preferred priority.


## Delete a listener

You cannot delete a listener that is currently used by Vulture (this can be an ha-proxy process or an Apache worker). <br/>
<br/>You will first need to delete / modify configuration to remove the reference to the listener you want to delete.
