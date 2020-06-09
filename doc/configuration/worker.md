---
title: "Workers profiles"
currentMenu: worker
parentMenu: configuration
---

## Overview

Worker profiles are used to tune the number of process and thread Vuture will allocate for applications. Vulture is based on the **Apache MPM worker**. This Multi-Processing Module (MPM) implements a hybrid multi-process multi-threaded server. By using threads to serve requests, it is able to serve a large number of requests with fewer system resources than a process-based server. However, it retains much of the stability of a process-based server by keeping multiple processes available, each with many threads.

The most important directives used to control this MPM are ThreadsPerChild, which controls the number of threads deployed by each child process and MaxRequestWorkers, which controls the maximum total number of threads that may be launched.
See https://httpd.apache.org/docs/2.4/en/mod/worker.html for details.

By default Vulture allows a maximum of 400 clients, this is the Apache's httpd default.

## Performance settings

 - `Friendly name`: A friendly name for your Worker profile.
 - `Graceful Shutdown Timeout`: After a configuration change, the Apache configuration files must be reloaded. Vulture uses 'graceful restart'. This kind of restart waits that current active requests are processed, then perform the httpd restart. This can take some time if you have heavy traffic on vulture servers. This settings force a restart immediately after the given timeout, in second.
 - `Max Connections Per Child`: Do not change this setting (zero = unlimited) unless you known what you are doing or unless you experiment memory leak over time.
 - `Min Spare Threads`: Minimal number of spare threads available to handle request peaks. Default is 75.
 - `Max Spare Threads`: Maximal number of spare threads available to handle request peaks. Default is 250.
 - `Maximum number of processes`: Maximum number of processes Vulture will start for the worker. Default is 16.
 - `Number of threads for a child`: Maximum number of threads that a single process may start. Default is 25.

## HTTP/2 settings

Vulture's HTTP/2 implementation is based on Apache mod_http2 module. <br/>
Vulture requires TLS to enable HTTP/2: **You cannot use HTTP/2 over a unencrypted connection**. This is not a bug, it is a feature.<br/><br/>

HTTP/2 settings are defined in a httpd server context, so these settings are sets inside the worker profile.

 - `H2 Direct Mode`: Enable the HTTP/2 direct mode. This is a VirtualHost level directive
 - `Max Session Stream`: Maximum number of active streams per HTTP/2 session. Defaults to 100.
 - `Max Worker Idle Seconds`: Beyond this amount of time, in seconds, HTTP/2 worker will die.
 - `Maxixum Number of Workers`: Maximum number of HTTP/2 workers per process.
 - `MinimumNumber of Workers`: Minimum number of HTTP/2 workers per process.
 - `Modern TLS Only`: If enable, HTTP/2 may only be enable with TLS1.2 and secure ciphers and algorithms.
 - `Push Mode`: Enable the HTTP/2 push mode.
 - `Push priority`: HTTP/2 has the ability to push content "inside" the Web browser, even if the web browser do not have requested it yet. When push is enable, this setting defines the push priority for a given content-type. This is used to define which kind of content you want to push to browser, with a given priority. There are some example in the default Vulture HTTP/2 profile. Please note that directives with '#' are example and won't be processed by Apache. So remove the leading '#' to use them.
 - `Serialize Headers`: If enable, headers will be serialized like with the HTTP/1.1 format.
 - `Session Extra Files`: This directive sets maximum number of extra file handles a HTTP/2 session is allowed to use. A file handle is counted as extra when it is transferred from a h2 worker thread to the main HTTP/2 connection handling. This commonly happens when serving static files.
Depending on the processing model configured on the server, the number of connections times number of active streams may exceed the number of file handles for the process. On the other hand, converting every file into memory bytes early results in too many buffer writes. This option helps to mitigate that.
 - `Stream Maximum Memory`: This directive sets the maximum number of outgoing data bytes buffered in memory for an active streams. This memory is not allocated per stream as such. Allocations are counted against this limit when they are about to be done. Stream processing freezes when the limit has been reached and will only continue when buffered data has been sent out to the client. Default is 65536.
 - `TLS Cooldown Seconds`: This directive sets the number of seconds of idle time on a TLS connection before the TLS write size falls back to small (~1300 bytes) length. Default is 1 seconds.
 - `TLS Warmup Size`: This directive sets the number of bytes to be sent in small TLS records (~1300 bytes) until doing maximum sized writes (16k) on https: HTTP/2 connections. Default is 1048576.
 - `H2 Upgrade`: This directive toggles the usage of the HTTP/1.1 Upgrade method for switching to HTTP/2.
 - `Windows size`: This directive sets the size of the window that is used for flow control from client to server and limits the amount of data the server has to buffer. The client will stop sending on a stream once the limit has been reached until the server announces more available space (as it has processed some of the data). Default is 65535.

See HTTP/2 Apache directives for details: https://httpd.apache.org/docs/2.4/en/mod/mod_http2.html.

## KeepAlive

See https://httpd.apache.org/docs/2.2/fr/mod/core.html#keepalive for details.

## Bandwith

See https://httpd.apache.org/docs/trunk/mod/mod_ratelimit.html and https://httpd.apache.org/docs/2.4/fr/mod/mod_reqtimeout.html for details.
