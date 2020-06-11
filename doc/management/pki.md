---
title: "PKI management"
currentMenu: pki
parentMenu: management
---

## Overview

You can manage the Internal Vulture's PKI from "Management / PKI".
During bootstrap process, of a `master node` Vulture will initialize an internal PKI and issue two X509 digital certificates:
 - One self-signed ROOT CA
 - One certificate associated to mongoDB and GUI apache httpd listeners

> The validity period of ROOT CA is 20 years. The validity period of other certificate is 5 years. <br/>
> For new nodes, the certificate is automatically issued when creating the new node in the GUI. The certificate will be downloaded by the slave node during its bootstrap process.

## Issuing a certificate

### "Create a certificate"

Using this view you can issue a certificate based on information you will provide in the form.
All the fields are mandatory:

* `Common Name` : The X509 "CN" field of the certificate.
* `Organisation` : Your organization name, X509 field "O".
* `Organizationnal Unit` : Your organization unit, X509 field "OU".
* `Country` : ** 2 letters ** representing your country code, X509 field "C".
* `State or Region` : Your state or region, X509 field "ST".
* `Locality` : Your city, X509 field "L".

These certificates are signed by the internal self-signed root CA of Vulture. They can be used in any TLS Vulture interfaces. If you need to expose TLS listener on the Internet, we recommand to use certificate issued by a "real" certificate authority. See below.<br/>
<br/>
**Note**: Do not forget to fill the certificate chain list (and the CRL, if OCSP cannot be used for any reason). See below.
<br/><br/>

#### Managing certificates

You can edit some attribute of a given certificate:

 - `Friendly name`: To display a friendly name into the GUI, instead of the certificate's DN.
 - `X509 Certificate chain file`: You MUST copy 'n paste the PEM encoded certificate chain here.
 - `Use the following CRL`: You MAY copy 'n paste the PEM encoded CRL associated to the certificate. This is useful for certificates not signed by Vulture when OCSP is not an option.


All certificates signed by the internet root CA of Vulture can't be deleted, only revoked. Vulture has to be able to deny an user who provides a non valid certificate.<br/>


<br/>
#### "Sign a request"

Instead of filling a form, Vulture can sign external requests. <br/>
All you need to do is to copy & paste the PEM Certificate Signing Request (CSR).
> Please note that in this case, Vulture do not have the private key associated to the certificate.


#### "Import a certificate"

If you wish to use a "real" trusted digital certificate, you can import the certificate and its private key from this menu.
You will need to copy & paste:
- `X509 PEM Certificate`: The PEM encoded certificate
- `X509 PEM Private Key`: The PEM encoded key
- `X509 Certificate chain file`: The PEM encoded certification chain

Vulture accepts encrypted private keys. At import time, Vulture will ask you the passphrase `only to check that you know it`. The passphrase will never be kept by Vulture. Please note that using encrypted private key will require you to type in the passphrase each time you stop or start a Vulture listener using this key. These listeners also won't be started automaticaly after a node reboot.


#### Managing trust inside Vulture

If you want Vulture to trust specific CA certificates, you can import them from the "Trusted CAs" tab. You will need to use a friedly name to reference the CA certificate as well as the PEM encoded certificate. <br/>

You can import multiple certificates in one time:
 - Use ";" to separate multiple fiendly names.
 - Copy & paste all your PEM encoded CA certificate in the same order.

> These CA certificates will be placed in /home/vlt-sys/Engine/conf/certs/<br/>
> They will be used by SSLProxyCACertificatePath in Apache configurations and whenever TLS is required to connect to a remote service (LDAP, MongoDB, ...).
