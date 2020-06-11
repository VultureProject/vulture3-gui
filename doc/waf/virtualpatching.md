---
title: "Virtual Patching"
currentMenu: virtualpatching
parentMenu: waf
---

**Virtual patching** can understand Acunetix, Qualysguqrd WAS and OWASP ZAP Proxy

From the log interface, it's possible to setup a whitelist or blacklist of specific fields for a given application. <br/>Then, those rules can be edited in the `Blacklist` or `Whitelist` menu.

For each application, a blacklist and a whitelist are auto generated.

The way blacklist and whitelist works are the same. Each list contains multiples rules that can be toggled. At each change, reloading the application so that the configuration are taken in account is required.