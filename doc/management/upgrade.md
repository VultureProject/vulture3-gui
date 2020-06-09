---
title: "Upgrade"
currentMenu: upgrade
parentMenu: management
---

## Overview

On the Vulture's main GUI or from the [Node Management form](/doc/management/nodes.html), you may notice messages telling you that Vulture needs upgrade.<br/>
This works with a hourly crontab that queries https://download.vultureproject.org and compares your current version of Vulture with the latest one available on the project's website.

## Upgrade process
When an update is available, you just have to click on 'upgrade' to upgrade the outdated component:
 - It may be an update for the Vulture-Engine (Vulture's version of Apache httpd + mod_vulture)?=.
 - It may be an update for the Vulture-GUI (Vulture's GUI python code).

`If both Vulture-GUI and Vulture-Engine updates are available, you MUST upgrade the two components, starting with Vulture-GUI`.<br/>
Please notice that you should never reload any worker configuration if both Engine and GUI are not up-to-date.<br/>
**This may cause side-effect: For example, Vulture-GUI may insert special directives in Apache worker's configuration, but these directives will be unknown by the Vulture-Engine, that will refuse to start**.

Vulture-GUI updates may affect system as they can:
  - Create / modify existing config on the filesystem.
  - Install or remove FreeBSD packages, via "pkg install" / "pkg remove".
  - Download and install Vulture-LIBS, which contains the Python virtual environment for GUI as well as some compiled libraries required by Vulture.

The embedded compiled libraries are, as of version 1.56 of Vulture, the following:
 - libgcc_s.so.1
 - libquadmath.so.0
 - libgfortran.so.3
 - liblapack.so.4
 - libblas.so.2
 - libopenblas.so.0
 - libopenblasp.so.0

These libraries are available in FreeBSD packaging, but they imply installing "dangerous" packages such as the gcc compiler.
So we preferred to manually embed these libraries into Vulture-LIBS.<br/>
They are placed into /usr/local/lib/vulture/.

When you click on upgrade, the GUI will wait until update is over. Depending of your Internet connection speed and the performance of your Vulture server, it may take some time.<br/>
The GUI may enter into a timeout and display an HTML 504 error message. This is harmless, just wait a couple of minutes and try later accessing the GUI.<br/>
If something goes wrong, check out the logs.


## Cluster upgrade

In cluster configuration, you have to repeat the upgrade process on each node. <br/>
**WAIT FOR A NODE TO FINISH UPDATE BEFORE LAUNCHING UPDATE ON ANOTHER NODE**.


## Technical details

You can upgrade by hand with the following commands:<br/>
```
$ /home/vlt-sys/scripts/install_updates gui
$ /home/vlt-sys/scripts/install_updates engine
```

With those commands, you will see what's happenning and check if an error occured during the upgrade process.

# Major FreeBSD UPGRADE (11.1 -> 11.2)

Follow these guidelines to upgrade, for example, from FreeBSD-11.1 to FreeBSD-11.2

## Stop redis on all nodes
Stop Redis : This needs to be done on every nodes at the same time
```
service redis stop  && service sentinel stop
```
 
## Upgrade FreeBSD
```
pkg update        
pkg upgrade      
freebsd-update fetch
freebsd-update install
freebsd-update upgrade -r 11.2-RELEASE
```
 
## Upgrade Vulture libraries
 ```
 - cd /tmp
 - rm ./Vulture-LIBS.tar.gz
 - /usr/local/bin/wget https://download.vultureproject.org/v3/11.2/Vulture-LIBS.tar.gz
 - cd /home/vlt-gui
 - rm -rf ./env
 - /usr/bin/tar xf /tmp/Vulture-LIBS.tar.gz
 - /usr/sbin/chown -R vlt-gui:vlt-gui /home/vlt-gui/
 - /bin/sh /home/vlt-gui/lib-11.2/install.sh
 ```
 
## Reboot and finish installation
```
 - shutdown -r now
 - freebsd-update install
```

## Vulture upgrade
```
 - /home/vlt-sys/scripts/check_updates.hour
 - /home/vlt-sys/scripts/install_updates gui
 - /home/vlt-sys/scripts/install_updates engine
```


# Major FreeBSD UPGRADE (11.2 -> 12.0)

Follow these guidelines to upgrade your Vulture from FreeBSD-11.2 to FreeBSD-12.0.

**Please follow this steps carefully !**

## Stop redis on all nodes
Stop Redis : This needs to be done on every nodes at the same time
```
service redis stop  && service sentinel stop
```

## Upgrade FreeBSD
```
freebsd-update fetch -F
freebsd-update install
freebsd-update upgrade -r 12.0-RELEASE
freebsd-update install
pkg update -f && pkg upgrade -y
```

## Fix potential missing library & reboot
 ```
 - find / -name "libgdbm.so.*" | grep so.4 || ln -s /usr/local/lib/libgdbm.so.6 /usr/local/lib/libgdbm.so.4
 - shutdown -r now
 ```

## Continue FreeBSD upgrade, upgrade GUI & Engine, and reboot
```
freebsd-update install
/home/vlt-sys/scripts/check_updates.hour
/home/vlt-sys/scripts/install_updates engine
service vulture stop
/home/vlt-sys/scripts/install_updates gui
pkg update -f && pkg upgrade -y
freebsd-update install
shutdown -r now
```

## Finish packages and libraries upgrade
**At reboot, the mongod service should be stopped.**

**Also, you have to install the mongodb34 package because mongodb32 is not supported on FreeBSD 12.0.**
```
pkg install -y mongodb34
service mongod start
cd /tmp
rm -f ./Vulture-LIBS.tar.gz
wget https://download.vultureproject.org/v3/12.0/Vulture-LIBS.tar.gz
cd /home/vlt-gui
rm -rf ./env
tar xf /tmp/Vulture-LIBS.tar.gz
./lib-12.0/install.sh
reboot
```

**After this last reboot, your Vulture should work properly.**
