---
title: "Users management"
currentMenu: users
parentMenu: management
---

## Overview

Vulture GUI users are authenticated against the internal MongoDB Repository. You can add or remove user from this view.
When creating a user, you will have to choose its group membership.

 > Note: You can use the internal MongoDB Repository as an authentication backend to protect your web application.

The following table describes permissions associated to groups:

<table border="0" cellspacing="0"><colgroup width="395"></colgroup> <colgroup span="4" width="174"></colgroup>
<tbody>
<tr>
<td align="center" valign="middle" bgcolor="#808080" height="34"><b><span style="color: #ffcc00; font-size: medium;">Fonction</span></b></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#808080"><b><span style="color: #ffcc00; font-size: medium;">Administrator</span></b></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#808080"><b><span style="color: #ffcc00; font-size: medium;">Application Manager</span></b></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#808080"><b><span style="color: #ffcc00; font-size: medium;">Security Manager</span></b></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#808080"><b><span style="color: #ffcc00; font-size: medium;">System Manager</span></b></td>
</tr>
<tr>
<td align="center" valign="middle" bgcolor="#EEEEEE"height="26">Balancer config</td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span></span></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
<td align="center" valign="middle" bgcolor="#EEEEEE">x</td>
</tr>
<tr>
<td align="center" valign="middle" height="26">Proxy Balancer config</td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td align="center" valign="middle"></td>
<td align="center" valign="middle"></td>
</tr>
<tr>
<td align="center" valign="middle" bgcolor="#EEEEEE" height="26">Listener management</td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
</tr>
<tr>
<td align="center" valign="middle" height="26">Network services management</td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td align="center" valign="middle"></td>
<td align="center" valign="middle"></td>
<td align="center" valign="middle">x</td>
</tr>
<tr>
<td align="center" valign="middle" bgcolor="#EEEEEE" height="26">Portal template management</td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
</tr>
<tr>
<td align="center" valign="middle" height="26">Statistics & diagnostic</td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
</tr>
<tr>
<td align="center" valign="middle" bgcolor="#EEEEEE" height="26">Users management</td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
</tr>
<tr>
<td align="center" valign="middle" height="26">ACL management</td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td align="center" valign="middle"></td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td align="center" valign="middle"></td>
</tr>
<tr>
<td align="center" valign="middle" bgcolor="#EEEEEE" height="26">TLS Profiles</td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
</tr>
<tr>
<td align="center" valign="middle" height="26">PKI Management</td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td align="center" valign="middle"></td>
<td align="center" valign="middle"></td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
</tr>
<tr>
<td align="center" valign="middle" bgcolor="#EEEEEE" height="26">Repository management</td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
</tr>
<tr>
<td align="center" valign="middle" height="26">WAF management (policy)</td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td align="center" valign="middle"></td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td align="center" valign="middle"></td>
</tr>
<tr>
<td align="center" valign="middle" bgcolor="#EEEEEE" height="26">WAF management (rules)</td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
</tr>
<tr>
<td align="center" valign="middle" height="26">Cluster, Nodes and updates</td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td align="center" valign="middle"></td>
<td align="center" valign="middle"></td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
</tr>
<tr>
<td align="center" valign="middle" bgcolor="#EEEEEE" height="26">Application management</td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
</tr>
<tr>
<td align="center" valign="middle" height="26">URL rewriting</td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle"><span>x</span></td>
<td align="center" valign="middle"></td>
<td align="center" valign="middle"></td>
</tr>
<tr>
<td align="center" valign="middle" bgcolor="#EEEEEE" height="26">Worker profiles</td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td style="text-align: center;" align="center" valign="middle" bgcolor="#EEEEEE"><span>x</span></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
<td align="center" valign="middle" bgcolor="#EEEEEE"></td>
</tr>
</tbody>
</table>
