---
title: "Response header settings"
currentMenu: response_header
parentMenu: app
---

## Overview

From this menu you can manage the response headers, sent from the Web application to client's web browser.<br/>
This feature is useful to add/modify headers sent by the web application, before they propagate to clients.<br/>
A typical usage of this feature is to modify response header of the backend.<br/>

It is based on the Apache module [mod_headers](https://httpd.apache.org/docs/current/en/mod/mod_headers.html#header)


## Response Headers

Basically you can do here everything you can do with Apache "Header" directive.

Click on "Add an entry" to create a new rule.
<br/>You will notice a toggle button before each rule: It allows you to enable / disable rule without having to delete it.

In the following example, we add some security headers and alter the 'Location' content when an HTTP 302 redirection occurs on backend:


![Headers](/doc/img/response_headers.png)
