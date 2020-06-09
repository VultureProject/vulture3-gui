---
title: "Troubleshooting"
currentMenu: troubleshooting
parentMenu: troubleshooting
---

## Debug mode Vulture

If an error occurs, you can check the logs: [Log Viewer](/doc/management/logs.html)<br/>
For advenced debugging you can activate the debug mode:<br/>

### Vulture-GUI
In the file `/home/vlt-gui/vulture/vulture/settings.py` and update:
`DEBUG = False` to: `DEBUG = True`

Then reload the Apache configuration with the following command:
```
/home/vlt-sys/Engine/bin/httpd -f /home/vlt-sys/Engine/conf/gui-httpd.conf -k restart
```

### Vulture-Portal
In the file `/home/vlt-gui/vulture/portal/settings.py`, and update:
`DEBUG = False` to: `DEBUG = True`

Then reload the Apache configuration with the following command:
```
/home/vlt-sys/Engine/bin/httpd -f /home/vlt-sys/Engine/conf/portal-httpd.conf -k restart
```

<i class="fa fa-warning">&nbsp;&nbsp;</i>Be careful in production, if you active the debug mode on the portal, all user will see the debug informations in case of error during an authentication.

## ESX image: "File xxxx.vmdk was not found / VMware ESX cannot find the virtual disk xxxx.vmdk"

If you encounter this error, please follow these steps:

 - Connect to your ESX through ssh (ssh needs to be enable first via vcenter),
 - Go to your VM datastore,
 - Execute the following command on the disk: vmkfstools -i disk.vmdk Disk.vmdk,
 - Detach disk.vmdk via vcenter and attach Disk.vmdk


## Backup and Restore Vulture's MongoDB Internal database

If `mongod` service is not terminated correctly (like when a hard shutdown occurs), it will fail to start on the next boot. This issue comes from MongoDB's storage engine, WiredTiger, which keeps its cache in memory.

To prevent Vulture from stopping to work. We wrote a cronjob that creates a mongo dump from Vulture database.

This job is ran every hour and only keeps the last two backups which are located at: `/var/db/mongodb_dumps/`.

**WARNING: only vulture database is dumped. If you want a backup of the log database you need to run your own scripts.**

### Restore database

If your MongoDB server refuses to start, there are two scripts located at `/home/vlt-sys/recover/` that will restore the vulture database.

You can run those scripts with `root` user on your vulture nodes depending on which status they have in the MongoDB Replicatset in the following order:


1) **If you have a Vulture cluster, for each of your mongoDB secondary nodes**, you need to run:
    - `sh /home/vlt-sys/recover/recover_mongo_secondary.sh`


2) **For your mongoDB primary node**, you need to run:
    - `sh /home/vlt-sys/recover/recover_mongo_primary.sh [optional mongo dump archive path] [-6 if IPv6]`.
    - By default the script picks the most recent dump in `/var/db/mongodb_dumps/` but you can specify another mongo dump archive.
    - If your Vulture is configured to use IPv6, just tape *-6* as second argument, if it is the case but you don't want to specify a dump archive, simply tape :
     -  `sh /home/vlt-sys/recover/recover_mongo_primary.sh "" -6`


If you don't have a Vulture cluster and the script ran successfully your Vulture should be back to normal.

If you have a cluster you need to **re-join** every mongoDB secondary inside the Vulture cluster from GUI in [Vulture Management -> Node](/doc/management/nodes.md).

The reason why is secondary nodes are not synced with the primary anymore. By adding them back to the cluster, Vulture will contact them and sets them as secondary MongoDB nodes.
