---
title: "Installation guide"
currentMenu: install
parentMenu: installation
---

## Prerequisites

You need to have a fully functional Vulture-OS system, installed either with the OVA/ESX image or with the Vulture install script (See: [Getting Started](/doc/getting-started.html)).
<br/><br/>Once you've got Vulture-OS running, log in as 'vlt-adm'. **WARNING**: vlt-adm account do not have any password at this stage. A "secure" random password will be generated during the bootstrap process (see below).

`AFTER INSTALLATION, PLEASE READ the Hardening GUIDE` and **adjust [pf firewall configuration](/doc/install/security.html) as it is permissive by default !**


## Bootstraping Vulture

During this step, Vulture will be downloaded and installed on top of Vulture-OS.
#### Prerequisites

Vulture requires an Internet connection to download FreeBSD & Vulture's updates. You can use an HTTP Proxy if needed. <br/>
Please note that the VultureProject website is not (yet) IPv6 ready - So you will have to use an IPv6 enabled HTTP Proxy if you want to bootstrap Vulture from an IPv6 network. <br/>
<br/>
#### Let's go !

Launch the bootstrap process with `sudo /home/vlt-gui/env/bin/python /var/bootstrap/bootstrap.py`. <br/>
You can also use a config file to bootstrap Vulture. This file is located at: /var/bootstrap/vulture_conf.json <br/>
vulture_conf.json:
<pre style="font-size: 12px;line-height: 15px;">
{
	"ready"          : "",			<span style="color:red;">Y</span>
	"confirm_license": "",			<span style="color:red;">OK</span>
	"keymap"         : "",			<span style="color:red;">ex: fr.iso.acc.kbd</span>
	"hostname"       : "",			<span style="color:red;">Hostname of the node</span>
	"proxy"          : "",			<span style="color:red;">If proxy, set the url (without http/https://)</span>
	"interface"      : 0,			<span style="color:red;">Interface to configure (0, 1, 2)</span>
	"ipv4_configure" : "",			<span style="color:red;">Configure IPv4 ? Y/N</span>
	"ipv4_dhcp"      : "",			<span style="color:red;">IPv4 DHCP Y/N</span>
	"ipv6_configure" : "",			<span style="color:red;">Configure IPv6 ? Y/N</span>
	"network_configuration": {
		"inet"      : "",			<span style="color:red;">IPv4 Address</span>
		"netmask"   : "",			<span style="color:red;">IPv4 Netmask</span>
		"gateway"   : "",			<span style="color:red;">IPv4 Gateway</span>
		"nameserver": "",			<span style="color:red;">DNS Nameserver</span>
		"inet6"     : "",			<span style="color:red;">IPv6 Address</span>
		"gateway6"  : ""			<span style="color:red;">IPv6 Gateway</span>
	},
	"ntp"           : "",			<span style="color:red;">NTP (default, blank)</span>
	"vulture_config": 0,			<span style="color:red;">0: Master Node; 1: Node</span>
	"node_config"   : {
		"primary_hostname": "",		<span style="color:red;">Primary hostname of the cluster</span>
		"primary_ip"      : "",		<span style="color:red;">Primary IP address</span>
		"cluster_password": ""		<span style="color:red;">Node password to join cluster</span>
	},
	"email_address"   : "",			<span style="color:red;">Email address for registration key</span>
	"registration_key": "",			<span style="color:red;">Registration key: will not be used.</span>

	"pki"    : {					<span>Ex:</span>
		"country"          : "",	<span style="color:red;">FR</span>
		"state"            : "",	<span style="color:red;">France</span>
		"city"             : "",	<span style="color:red;">Lille</span>
		"organization"     : "",	<span style="color:red;">VultureProject</span>
		"organization_unit": ""		<span style="color:red;">VultureProject</span>
	},
	"admin": {
		"username"  : "",			<span style="color:red;">admin</span>
		"password"  : "",			<span style="color:red;">*******</span>
		"repassword": ""			<span style="color:red;">*******</span>
	}
}
</pre>

All value are optional. If a value is not filled, the bootstrap will ask you the value.<br:>
To launch the bootstrap with the configuration file:<br/>
`/var/bootstrap/bootstrap.py --config /var/bootstrap/vulture_conf.json`

<br/>
During the process Vulture will configure the system and install Vulture <br/>
You will be guided through several steps:
- Keyboard configuration
- Network and proxy configuration
- Choice of the installation mode:
    * Create a new Vulture cluster
    * Join an existing one
- Vulture registration (a valid email address is required to receive an activation code)
- Vulture Downloading
- Internal PKI initialization
- "GUI admin" user & password definition
- "vlt-adm" password randomization
- Start of Vulture processes

<br/>
Installation process can take several minutes, depending of your internet connection speed. <br/>
Be careful during PKI initialization: `The country field needs to be on 2 characters, "FR" for example`. <br/>
<br/>
 - **IMPORTANT**: If you are using ZFS as filesystem, you need to add zfs_enable="YES" in /etc/rc.conf
 - **IMPORTANT**: Vulture needs to be rebooted after bootstrap
<br/><br/>

When everything is good, Vulture GUI should be accessible at https://your_ip_adress:8000.
<br/>
<br/>
The `root` account is not allowed to login over SSH. Please `log in with 'vlt-adm'` and become root with `sudo csh` when needed. During normal operation, SSH or console access is not needed, as a lot of things are available through the Vulture GUI. <br/>
<br/>

## Vulture GUI

Vulture is fully manageable from the Web GUI. It is listening on TCP port 8000 by default. <br/>
Vulture GUI requires a TLSv1.1 compatible web browser. Best experience with Firefox! <br/>
<br/>
You can login into the GUI with the username and password defined during the bootstrap process: <br/>

![Vulture GUI](/doc/img/login.png)
