---
title: "URL Rewriting"
currentMenu: rewriting
parentMenu: network
---

## Overview

When Vulture receives an HTTP request, you can modify the requested URL before processing it. <br/>
You can create rules that apply on all applications or only to the specified ones.

Click on "Add an entry" to create a new URL rewriting rule:

 - `Friendly name`: A friendly name for the rules
 - `This is a template`: Check that if you wan to create a rules template that you can clone later
 - `Apply this rule on`: If you select nothing, the rule applies on all applications. You can select multiple applications by pressing "ctrl + left click"

If you have multiple rules, Vulture will apply them in the following way:
 1. Rules that apply to all applications are activated first, in the httpd "<Server>" context
 2. Rules that apply to a specific application are then activated, in a httpd "<VirtualHost>" context

## Rewriting policy

You can combine multiple conditions and action in a rule policy.<br/>
You can drag'n drop element in the GUI.
Here is an example: <br/>
<br/>
![URL Rewriting](/doc/img/url-rewriting.png)

In this example, if we found "Mozilla" in the HTTP User-Agent, we replace the URL by https://www.google.fr and then we perform an HTTP 302 redirection ([R] flag).<br/>
Consult [mod_rewrite](https://httpd.apache.org/docs/current/fr/mod/mod_rewrite.html) for details on URL rewriting.
