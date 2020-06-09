---
title: "Diagnostic"
currentMenu: diagnostic
parentMenu: getting-started
---

## "Diagnostic" menu

Vulture has a powerful built-in diagnostic framework that aims to detect any problem inside a Vulture cluster. The diagnostic is run every minute by a "vlt-gui" crontab. It checks several vital points for Vulture:
 - Connection to download.vultureproject.org
 - Disk space
 - File ownership and permissions
 - MongoDB, Redis, Sentinel... connection and access
 - Lack of system update or vulnerabilities on installed packages
 - ...

If a problem is detected, Vulture will display a bell in the GUI:<br/>
![](/doc/img/bell.png)<br/>
<br/>
<br/>
You can click on the bell to have an overview of the problem:<br/>
![](/doc/img/vuln.png)<br/>
<br/>

In case of a major disaster on a Vulture node, you can launch a diagnostic from the console:<br/>
`/home/vlt-gui/env/bin/python /home/vlt-gui/vulture/testing/testing_client.py --output detailed`
```
*-------------------------------------------------------------------------*
| Module                               | Time (seconds)  | Failed | Total |
*-------------------------------------------------------------------------*
| Connection to VultureProject Website | 0.159658908844  | 0      | 1     |
| Node System Status                   | 0.0537858009338 | 0      | 5     |
| Cluster Interconnection              | 0.754734992981  | 0      | 6     |
*-------------------------------------------------------------------------*
```
In case of a test failure, Vulture will throw an exception and explain what the problem is. <br/>
<br/>
`Please contact support@vultureproject.org if you want us to add specific control inside the diagnostic system.`
