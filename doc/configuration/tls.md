---
title: "TLS profiles"
currentMenu: tls
parentMenu: configuration
---

## Overwiew

Create a TLS profile to implement TLS and encrypt communication between **clients** and Vulture.<br/>
This profile will be associated to a listener in the [application's listener panel](/doc/app/listener.html).<br/>

**Note:** If you want TLS between Vulture and your **web servers**, this can be done directly from the [application's backend panel](/doc/app/backend.html).

<br/>
Vulture is currently using OpenSSL, via mod_ssl, to implement TLS. Migration to GnuTLS is in progress. <br/>

## Create a TLS profile

### General settings and Ciphers

 - `Friendly name`: A friendly name for the profile.
 - `SSL Crypto Engine`: Vulture identifies SSL crypto devices that are installed on your server. If nothing is found, "Software engine" will be used.
 - `X509 Certificate to use`: The server certificate used by Vulture. The certificate should have been created or imported before, via the [internal PKI](/doc/management/pki.html).
 - `Accepted protocols`: Minimum SSL/TLS version. If the client do not support this minimal version, the connexion will be refused. Consult [mod_ssl SSLProtocol](https://httpd.apache.org/docs/current/fr/mod/mod_ssl.html#sslprotocol) documentation for details.
 - `Accepted ciphers`: Encryption and hashing algorithms that Vulture should accept or refuse(!). Consult [mod_ssl SSLCipherSuite](https://httpd.apache.org/docs/current/fr/mod/mod_ssl.html#sslciphersuite) documentation for details.
 - `Honor Cipher Order`: If enabled, vulture tls preferences will be proposed to the client ordered by descending security level: The first algorithm that satisfies both client and vulture will be chosen. This prevents client to force a negotiation with weak algorithms.

 > **Note: If you are using HTTP/2, you MUST enable TLS into your application and use a TLSv1.2 profile**

Here is a reasonably secure SSLCipherSuite that should work with modern web browsers :
```
ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!3DES:!MD5:!PSK
```

### Client certificates

You can configure Vulture to require a valid client certificate. <br/>
Such a certificate should be installed into the client's web browser and its Certification Authority must be the one expected by Vulture.

There are several options for this feature:

 - `Not Required`: This is the default: No client certificate are required.
 - `Optional, but need to be valid`: The client MAY present a valid certificate, but it is not mandatory.
 - `Required` : The client MUST present a valid certificate, but it is not mandatory.
 - `Optional, and do not need to be valid` : The client MAY present a certificate and the certificate can be invalid (not trusted). `This should never be used.`

If a certificate is optional or required, you need to configure the following:
 - `Accepted CA`: Copy and paste PEM encoded CA certificates that you consider valid for client authentication.
 - `If no client certificate, redirect to`: If the client does not present a certificate, redirect it to the specified URI.

Vulture automatically checks its internal CRL before accepting certificates. If you want to manage custom CRL files, you will need to copy and paste the PEM encoded CRL into the corresponding TLS server certificate used by Vulture. This can be done from the [PKI panel](/doc/management/pki.html).

### OCSP

If you want Vulture to check for CRL (Certificate Revocation List) through the OCSP protocol, you can enable `OCSP responder verification`.<br/>
This option enables OCSP validation of the client certificate chain. <br/>
If this option is enabled, certificates in the client's certificate chain will be validated against an OCSP responder after normal verification (including CRL checks) have taken place.<br/>
<br/>
The OCSP responder used is either extracted from the certificate itself, or derived by configuration
<br/>
See https://httpd.apache.org/docs/current/en/mod/mod_ssl.html#sslocspenable for details.


 - `Default OCSP responder`: This sets the default OCSP responder to use. If SSLOCSPOverrideResponder is not enabled, the URI given will be used only if no responder URI is specified in the certificate being verified.
 - `Override OCSP responder with default ?`: If set, Vulture will ignore the URI specified in the certificate being verified and will use the default responder instead.
 - `OCSP responder timeout`: This option sets the timeout for queries to OCSP responders, in seconds.


### Advanced

You can specify custom modSSL directives inside the Vulture configuration:
 - `Custom mod_ssl directives for virtualhost context` will be placed in the application's VirtualHost context.
 - `Custom mod_ssl directives for application context` will be placed in the application's VirtualHost context, under a **<Location */public_dir*>** section.
