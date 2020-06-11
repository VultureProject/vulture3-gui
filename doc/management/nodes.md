---
title: "Managing Nodes"
currentMenu: nodes
parentMenu: management
---

## Overview

From the "Vulture Management / Nodes" view you can manage the global Vulture Cluster:
 - Add or remove nodes
 - Switch a node from master to slave

Vulture Cluster is based on [MongoDB ReplicaSet](https://docs.mongodb.com/manual/core/replica-set-architectures/) to share Vulture configuration between nodes. This "database" is referenced in Vulture as the `Internal MongoDBEngine`. <br/>Other critical components in Vulture are [Redis and Sentinel](https://redis.io/topics/sentinel). <br/>
>Communication between Vulture nodes is done through REST API calls on TCP port 8000. Communication are secured with TLS1.2 and a client certificate (/var/db/mongod/mongod.pem).<br/><br/>
>MongoDB is listening on *:9091
>Redis is listening on *:6379
>Sentinel is listening on *:26379

## Nodes management

### Nodes list

This page displays the list of all nodes within the cluster and shows a number of useful informations:

* `Name`: The hostname of the node. Vulture nodes use this name to contact node, so it must be resolvable.
* `Engine Version`: Version of the Vulture Apache Engine.
* `GUI Version`: Version of the Vulture GUI.
* `Member of MongoDB ReplicaSet`: Indicates if the node is part of a MongoDB Replicaset, as well as the node status (PRIMARY or SECONDARY).
* `Member of Redis Cluster`: Indicates if the node is part of a Redis Cluster, as well as the node status (MASTER or SLAVE).

> Vulture Apache Engine is a custom version of Apache httpd. It includes specific vulture modules (mod_vulture, mod_svmX...).

Depending if the node status, several actions are available:

- **If the node is a mongoDB PRIMARY** you can't do anything :-)
- **If the node is a mongoDB SECONDARY** you can:
    - Promote it to PRIMARY
    - Remove it from ReplicatSet

When a node is removed from the Replicaset, its MongoDB Database is not synced anymore with the rest of the cluster. This can be usefull if you want to set up a new Vulture Node, with identical configuration as the cluster: Add a new node, wait for sync, remove it, remove other nodes from its configuration. And you've got a single node with the same configuration as the working cluster. <br/>
It is good practice to remove a node from the cluster before stopping it: If you don't remove the node, remaining nodes will always try to contact it, and this slows down the GUI (there is no impact on Vulture's Apache performance for Web applications).
<br/>

**If the node is a Redis SLAVE** you can force a Redis failover to promote it as a MASTER. See https://redis.io/commands/cluster-failover <br>
<br/>
You can't delete a node that is either a MongoDB PRIMARY or a Redis MASTER.

`There is no data loss during MongoDB or Redis switch`: The cluster still works perfectly. Note that MongoDB requires 3 nodes to avoid any failure during switches. So it is not a good idea to start a Vulture cluster with only 2 nodes: If the PRIMARY crashes, the SECONDARY may not be promoted as PRIMARY and manual intervention may be required. <br/>
<br/>
So with Vulture it is best to have just 1 node, or at least 3. <br/>


### Adding a node

When adding a node, you just need to define its hostname and click 'Save'. Once done, the node will apear as "pending" in the node list and a temporary key is printed on screen. This key will be required during the bootstrap process of this node: The master node won't accept the new node without a valid key.

### Troubleshooting

If a node is not a member of the mongoDB Replicaset, you can follow the following procedure to manually add it to the cluster:
```
mongo –ssl –sslPEMKeyFile /var/db/mongodb/mongod.pem <primary_node>:9091/vulture
rs.status()                     #This will shows the list of node inside the ReplicaSet
rs.add("<missing_node>:9091")     #This will add the missing_host to the ReplicaSet
```
Replace "primary_node" by the IP of your primary node.<br/>
Replace "missing_node" by the IP of the node you wish to add in the ReplicaSet.


### Node properties

When you click on a node, you will be able to edit some network attributes:

 - `Node name`: This is a read-only textarea, as you cannot modify the name of an existing node.
 - `Default IPV4 Gateway`: You can set here the default IPV4 gateway for the node.
 - `Default IPV6 Gateway`: You can set here the default IPV6 gateway for the node.
 - `Static route`: You may define additional static routes here.

For static routes, refers to FreeBSD documentation when needed: https://www.freebsd.org/doc/handbook/network-routing.html.
Here is an exemple that defines 2 static routes, one on an IPV4 interface and another on a IPv6 interface.
```
static_routes="vlan1 vlan2"
route_vlan1="-net -inet6 fd00:1::/64 fd00:3::ffff"
route_vlan2="-net 192.168.2.0/24 192.168.2.1"
```

The first line defines "vlan1" and "vlan2" as persistent static routes. <br/>
Other lines set the configuration of both routes.

This configuration will be stored in `/etc/rc.conf.local`. After clicking on 'Save', Vulture will perform a `service routing restart`, thus resulting in a temporary lost of existing routes for a couple of seconds.<br/>
Avoid doing that when your are in production.
