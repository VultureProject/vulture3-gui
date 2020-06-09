---
title: "Content Rewriting"
currentMenu: content_rewrite
parentMenu: app
---

## Overview

From this menu you can manage the content rewriting rules. It allows Vulture to rewrite any part of your application's response, from headers to body. <br/>
If your web application compress its output, Vulture won't be able to rewrite content.
In this case, you will first have to deflate the content so that Vulture can apply rewriting rules.
To do so, you have to check the "Decompress backend" box.<br/>
If you want Vulture to compress content before sending it to clients, check the "Compress response" box.
<br/>
If you want to apply a rule only for specific content type(s), use the Content-Type option.<br/>

**Note**: If you want to decompress responses from backend and/or compress responses to clients all the time, just check the wanted box(es) and leave the "Substitute" and "With" fields blank.

## GZIP Management
The compression feature of Vulture is based on the Apache [deflate_module](https://httpd.apache.org/docs/2.4/en/mod/mod_deflate.html).<br/>

## Content rewriting
The rewrite feature of Vulture is based on the Apache [substitute_module](https://httpd.apache.org/docs/2.4/en/mod/mod_substitute.html).

## Example
In the following example, we inflate responses from backend and compress responses to clients for all webpages and all content-types, and apply the substitution rule.

![Rewrite](/doc/img/rewrite.png)
