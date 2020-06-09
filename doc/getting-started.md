---
title: "Getting started"
currentMenu: getting-started
---

## Get Started

Want to test Vulture in a minute ? Just download the pre-installed Vulture system
    - VMWare image: https://www.vultureproject.org/download/

Want to install Vulture on top of FreeBSD 11 ?
 - Download the installer script : https://www.vultureproject.org/download/
 - Then execute `/bin/sh ./vulture_installer.sh` on any FreeBSD 11 system (see prerequisites below)
 - At this stage, Vulture will be in the same state as with OVA or ESX Image
<br/>

The final step is to launch the bootstrap process: See the [Installation guide](/doc/install/steps.html) for details.<br/>
Don't forget to have a look at the [Security hardening guide](/doc/install/security.html) of Vulture.


## Prerequisites

Vulture runs on any physical or virtual system capable to run FreeBSD. <br/>
It requires a 64bit modern multicore CPU with 2GB of RAM (4GB recommended for reputation and machine learning) and 50Go of disk space.

Vulture requires the following partition scheme:
 - "swap" (2Go)
 - "/" (6Go)
 - "/home" (2Go)
 - "/var" (as much as you need for logs)

During the installation process, Vulture needs to contact download.vultureproject.org on TCP port 443.


