---
title: "RADIUS Repository"
currentMenu: radius
parentMenu: repositories
---

## Overview

Vulture can authenticate users against a Radius backend. This feature is built on top of the pyrad implementation (https://pypi.python.org/pypi/pyrad).
Thus Vulture supports all that pyrad supports: For now, only the md5-based challenge.
Radius support is very limited on Vulture and we do not encourage this method for now unless you are able to secure the communication between Vulture and your Radius server.

## RADIUS Backend

To add a radius authentication server you will need to provide the following information:

 - `Repository name`: A friendly name for the radius repo.
 - `Host`: The IP address of your radius server.
 - `Port`: The TCP port of your radius server.
 - `NAS_ID`: The Radius NAS identifier. This is a text string used by the Radius server to determine the policy to apply for radius request coming from Vulture.
 - `Authentication secret`: The shared secret used between Vulture and the Radius server.
 - `Max retries to authenticate clients`: Number of times to retry sending a RADIUS request in case of a network failure.
 - `Max timeout to authenticate clients`: Number of seconds to wait for an answer from the server.

When clicking on "Test authentication settings", you can test if your settings are good. Vulture will prompt for a login and a password and will try to authenticate against your Radius server.
If a problem occurs, Vulture will display the error message.
