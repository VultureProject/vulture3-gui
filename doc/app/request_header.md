---
title: "Request header settings"
currentMenu: request_header
parentMenu: app
---

## Overview

From this menu you can manage the requested headers, sent from client's web browser to Vulture. <br/>
This feature is useful to add/modify headers sent by the client, before they are transmitted to your web application.

It is based on the Apache module [mod_headers](https://httpd.apache.org/docs/current/en/mod/mod_headers.html#requestheader)

## Request Headers

Basically you can do here everything you can do with Apache "RequestHeader" directive.

Click on "Add an entry" to create a new rule.
<br/>You will notice a toggle button before each rule: It allows you to enable / disable rule without having to delete it.

A typical usage of this feature is to add the 'Host' header for backends that use NameVirtualhost:
 - In Backend's private IP you will configure something like http://192.168.1.1.
 - In this menu you will add the Header `Host: www.example.com` with "Add the header" / "Host" / "www.example.com" / "always".

![Headers](/doc/img/headers.png)
