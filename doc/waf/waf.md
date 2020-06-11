---
title: "Web Application Firewall"
currentMenu: waf
parentMenu: waf
---

## Overview

Vulture allows you to filter incoming and outgoing web trafic and block threats like injection, cross site scriping... and other attacks of the OWASP Top10.<br/>
It is relying on mod_security, mod_defender (fork of Naxsi), and mod_svm (Machine learning based on Support Vector Machines) to filter HTTP traffic.<br/>

mod_security has been improved to fit Vulture's clustered design.
mod_svm is the exclusive property of aDvens, and freely usable in Vulture.
mod_defender is freely available under a GPLv3 licence : https://github.com/VultureProject/mod_defender

All these filtering engines works together, and you don't have the complexity of managing 3 different engines: All is simplified in the Vulture GUI.
Another cool benefit of having mod_security and mod_defender is that you can create ruleset that mix MAXSI's syntax and mod_security's syntax, depending of what you want to achieve.

If a "abnormal request" is detected, mod_security or mod_svm or mod_defender will increment the score of the request.
If the request score reach the maximum accepted score, Vulture will block.

## Mod Security

mod_security is the historical filtering engine of Vulture. See https://modsecurity.org/ for details.
Note that Vulture uses a modified version of mod_security: We removed the support of DBM based collection files and uses redis instead. This improve performances and allow mod_security to run in cluster mode, sharing session's data between multiple nodes.

If a mod_security rule match, Vulture will increment the score of the request, as mod_svm and mod_defender do.

## Mod SVM

### Overview

mod_svm is an Apache module written by aDvens that implements non-supervised machine learning. It works by computing a mathematical representation of "good traffic" (Python code in GUI) and then, in realtime, by comparing incoming and outgoing requests against this representation.
The realtime code is handled by mod_svm, an Apache module developed in C-language.

Building the SVM (GUI side) is a long operation and needs strong CPU and RAM.
Checking an HTTP request / response against an existing SVM (mod_svm side) if blazing fast. If a "abnormal request" is detected, mod_svm will increment the score of the request, as mod_security and mod_defender do.

### Mode of operation

Mod_svm is composed of 4 modules. This modules are written in C and used the scikit-learn library proposed by the INRIA (French Institute for Research in Computer Science and Automation). <br>
This library is by default available in Python but we have extracted the mathematical core, written in C++ to use-it in an Apache module, written in C. <br>

At first, the learning Dataset have to be built in the "Logs" view with the button "Create dataset". Then, in the view "Dataset", the SVMs have to be generated from the Dataset. <br>
Finaly, they can be used by the applications in the "Security" tab. <br>

### Building the SVMs

The 4 SVMs are bidimensional, they each use an x and an y to create a dataset (an SVM) representing the legitimate area within a 2D graphic. <br>
For the first SVM, to create a dataset of (x and y) pairs, here is the algorithm used : <br>
```
uris = list
for each uri of logs:
    for each piece of uri.split_by('/'):
        uris.append( piece )
for each piece of uris:
    tmp_list = list
    for each piece2 of uris:
        tmp_list.append( levenshtein_distance(piece, piece2) )
    x = average(tmp_list)
    y = len( piece )
    dataset.append( [x , y] )
```
Levenshtein distance is the number of different characters between two words. For example, between "test" and "tent" the levenshtein distance is 1. <br>
This dataset is then used to generate an SVM with <b>sklearn</b>, more precisely an object <b>OneClassSVM</b>, which will be stocked in MongoDB, and subsequently used by Apache as <b>mod_svm2</b>.

The second SVM uses the same algorithm as the last one, the only difference is that the uris are not splitted by '/'. The pseudo code of the algorithm is : <br>
```
for each uri in logs:
    tmp_list = list
    for each uri2 in logs:
        tmp_list.append( levenshtein_distance(uri, uri2) )
    x = average(tmp_list)
    y = len( uri )
    dataset.append( [x , y] )
```
In the same way, this dataset is used to create an <b>OneClassSVM</b> object, which will be saved in MongoDB and written in Apache configuration as <b>mod_svm3</b>. <br><br>

The third SVM is totally different, we use the <b>HTTP status code</b> as x, and the <b>bytes received</b> (by Vulture) as y. <br>
This list of (x and y) pairs is then used to create an <b>OneClassSVM</b> object which will be saved in MongoDB and used to generate the Apache configuration. <br><br>

This fourth SVM uses the <b>HTTP status code</b> as x, and the <b>ratio between bytes sent and bytes received</b> (by Vulture) as y. <br>
This list of (x and y) pairs is then used to create an <b>OneClassSVM</b> object which will be saved in MongoDB and used to generate the Apache configuration. <br><br>

### Generate the Apache configuration

Within the C code of Apache modules, we use the C structures called "svm_model" and "svm_parameter" which have the same attributes as the python object OneClassSVM. <br>
So, to transmit this attributes from python object to C structure, we have identified their types in C code, and we directly export the attribute if it is an int or a float, and we use the "hexlify" function to export tables of floats or of integers. <br>

Then, within the C module, we re-convert all of this directives parameters to create the structures "svm_model" and "svm_parameter" which will be used to "predict" each received request. <br>

For the svm2 and svm3 modules, we have to export the list of all the uris that were used to create the dataset, to perform the levenshtein averages. <br>

The four configuration files are templated as vulture_svm{2,3,4,5}.conf and used by python (jinja) to generate the files in /home/vlt-sys/Engine/conf/svm directory. They are then used in application configuration file with the Apache directive "Include". <br>

### Apache modules

The svm2 and svm3 modules are in the <b>fixups</b> hook to retrieve and predict the requested url. <br>
The svm4 has 3 hooks, one in <b>fixups</b> to retrieve the request length, one in <b>input_filters</b> to retrieve request body length, and one in <b>output_filters</b> to retrieve the HTTP status code response from the application.
The prediction is then made in output_filter.
As svm4, svm5 has the same 3 hooks, but retrieves the bytes sent from the application response and makes prediction. <br>

If a prediction return -1, which means that the (x and y) pair is out of the legitimate area, an environment variable is set depending on the svm. For example, if in the svm2 the prediction result is -1, the "svm2" environment variable is set to "1". <br>

### Detection and blocking

Because the svm2 and 3 are in fixups, we use <b>mod_security</b> to increment the anomaly score depending on svm environment variables. <br>
For that, the following two directives are used :
*  SecRule ENV:SVM2 "@eq 1" "id:'21',t:none,pass,nolog,setvar:tx.inbound_anomaly_score=+%{tx.warning_anomaly_score},msg:'SVM 2 triggered'"
*  SecRule ENV:SVM3 "@eq 1" "id:'22',t:none,pass,nolog,setvar:tx.inbound_anomaly_score=+%{tx.notice_anomaly_score},msg:'SVM 3 triggered'"
If the "svm2" environment is equal to "1", the anomaly score will be incremented by the "warning_anomaly_score" value. <br>
If the "svm3" environment is equal to "1", the anomaly score will be incremented by the "notice_anomaly_score" value. <br>
If a rule matches, the corresponding message will be set in the "reason" variable and available in access logs. And if the anomaly score reaches the threshold (set in Policy settings), a 403 HTTP response code will be sent to the client. <br>
For the svm4 and 5, the anomaly score incrementation is made in Mod_Vulture's output filter. <br>
If the "svm4" environment variable is set, the anomaly score will be increased by the "warning anomaly score" value, same for the "svm5". <br>
If the anomaly score reaches the threshold, a 403 HTTP response code will be sent to the client. <br>

## Mod Defender

### Overview

mod_defender is a lightweight, blazing-fast and scalable web application firewall module for Apache. mod_defender is a fork of Naxsi, a WAF designed for NGINX.
It works on a whitelist approach: By default, everything is blocked and only "explicitely accepted traffic" is allowed. mod_defender uses a **main rules** configuration files, that contains regular expressions about well-known "attack pattern". When a main rule matches, the request's score is incremented. When the **blocking threshold** is reached, mod_defender will block the request.
One can considers main rules as "static blacklists": These rules doesn't evolve much.

In addition to main rules, mod_defender uses **basic rules** to explicitely whitelist good requests. These rules are unique to the website to protect.
Fortunately, they can be generated on an automatic way: mod_defender uses a ""**learning mode**": During learning, requests are not blocked: they are stored in a database (elasticsearch or mongodb) and then processed by a script that will build the basic rules.

### Mode of operation

mod_defender's functionalities are broadly similar to Naxsi's ones. It uses the same format for main, basic rules and score rules (Vulture do not uses score rules, but its internal scoring system, which mix scoring from mod_security, mod_defender and mod_svm).
This compatibility allows administrator to run tools like NXApi/nxtool to generate basic rules. When mod_defender is in learning mode, blocked requests are logged with detailed information in mongodb / elastic (GUI-1.44)


#### Configuration

mod_defender can be configured with specific <Location> blocs in Apache configuration, with the help of the following directives:

`MatchLog` : Path of the learning logfile. Default is /var/log/apache2/defender_match.log
`JSONMatchLog` : Path of the learning logfile in JSON format. Default is /var/log/apache2/defender_json_match.log
`RequestBodyLimit` : Maximum size of POST requests. Default is 128 KB.
`LearningMode` : On/Off, enable or disable the learning mode. Enabled by default.
`ExtensiveLog` : On/Off, enable or disable advanced learning mode (with the variable's content). Disabled by default (in Vulture, this is automatically enabled when LearningMode is enable)
`LibinjectionSQL` : On/Off, enable of disable generic detection of SQL Injection, using Libinjection.
`LibinjectionXSS` : On/Off, enable of disable generic detection of Cross Site Scripting, using Libinjection.
`CheckRule`: Rules that describe maximum accepted score (automatically managed by Vulture)

#### Limitation

Unlike other WAF, mod_defender and naxsi, do not run with a signature database.
Other specific features are:
 - mod_defender only inspect GET and POST / PUT requests
 - mod_defender only allow the following content-types: application/x-www-form-urlencoded, multipart/form-data and application/json

Inside Vulture, unlike Naxsi, if a invalid content-type is detected, mod_defender won't block: The anomaly score will be increased instead.
Inside Vulture we cover protection on other VERBS (like DELETE, HEAD, ...) with the help of mod_security and mod_svm.

#### Advantages

mod_defender has been developped with performance in mind. That's why its main logic is coded in C++11. Regular expression are not provided with any external libraries. Indeed "C++11 regex" is used inside mod_defender.
For hash tables, mod_defender uses C++11 unordered_map, one ot the best choice among STL containers: Maximum performance and less collisions.
mod_defender does not depend of any library, even those of Apache or NGINX. Thus, it is portable on almost any platform and may be used by other software as a reliable Web filtering engine.

Specifically, we paid attention to reduce at the maximum the number of copies of each part of HTTP requests. Moreover, to improve performance, mod_defender only works in lowercase (Request are transformed in lower case first).

Unlike mod_security, mod_defender threats incoming HTTP request's body in a "**spectator mode**": Request's body is read and a copy is made for inspection purposes. Once inspection is done and if no problem is found, the original body is sent to Apache. This avoids any problem related to charset decoding that may occurs later in the processing phase.


#### Blacklist

A main block rule uses the following format :

```
MainRule "str/rx:<pattern to match>" "msg:<message when match>" "mz:<zone to inspect>" "s:<score to apply>" id:<rule number>;
```

**pattern to match**
The pattern to match may be a regular expression (regex) or a string:
 - `rx:foo|bar`  : String "foo" of string "bar"
 - `str:foo|bar` : String "foo|bar".
 - `d:libinj_sql` : Scan for generic SQL injection patterns, using libinjection SQL
 - `d:libinj_xss` : Scan for generic XSS injection patterns, using libinjection XSS


Use string patterns instead of regex when possible, this is faster.
All strings must be written in lowercase as mod_defender converts all string to lowercase before processing.

**Message**
msg is a message that describes the rule in a comprehensive manner. This attribute is used in logs when a rule matches and thus explains the block reason.

**Zone to inspect**

`mz` means "match zone". It tells mod_defender where to look for the pattern.

 - `mz:BODY|URL|ARGS` means that the BODY, the URL (before the '?') and GET variables will be inspected
 - `mz:$HEADERS_VAR:Cookie` means that the rule will inspect the "Cookie" HTTP HEADER
 - `mz:$URL:/login|$ARGS_VAR:username` means that the GET parameter 'username' will be inspected when the request URL is '/login'

Name and extension of files may be specified in the zone `FILE_EXT` to inspect request during a file upload.


**Score**
`s` tells mod_defender which counter to increase, and by which amount, when the rule matches.
A rule may increment several counter at once.

  - `s:$SQL:8` will add '8' to the '$SQL' counter.
  - `s:$SQL:4,$XSS:4` will add '4' to the '$SQL' counter and '4' to the '$XSS' counter.

In the score rule, one can also use one of the following action: `BLOCK`, `DROP`, `ALLOW` or `LOG`.
The action will be applied when the pattern matches.


**Rule number**

`id` is the rule number which will be used by other basic rules to refer to this rule. The rule number is also present in logs when the rule matches.

**Negation**

It is possible to add the `negative` keyword to invert the action of the rule, so that the score will be applied if the rule do not match.


#### Whitelist

A basic accept rule uses the following format:
```
BasicRule wl:<main rules' id to disable> "mz:<zones to inspect>"
```

**Main rules' id to disable**

Tells mod_defender to deactivate blocking main rules. Main rules to deactivate are referenced by their respective ids.
Possible syntax are :

 - `wl:1000` disable the rule n°1000
 - `wl:1000,1001,1002` disable rules n°1000, 1001 and 1002
 - `wl:-1000` disable all rules except rule n°1000 and internal rules

**Zone to inspect**

`mz` means "match zone". It tells mod_defender where to look for the pattern. Match zone is optional: If not specified, the basic rule will apply to all request's zones.
Available match zones are :

 - `ARGS` : GET parameters
 - `$ARGS_VAR` : Name of a GET parameter
 - `$ARGS_VAR_X` : Regex that applies to the name of a GET parameter
 - `HEADERS` : HTTP headers
 - `$HEADERS_VAR` : Name of an HTTP header
 - `$HEADERS_VAR_X` : Regex that applies to the name of a HTTP header
 - `BODY` : BODY of a POST / PUT request
 - `$BODY_VAR` : Name of a parameter that belongs to the body of a POST / PUT request
 - `$BODY_VAR_X` : Regex that applies to the name of a parameter that belongs to the body of a POST / PUT request
 - `URL` : URL of the asked resource, before the '?'
 - `$URL` : Specific URL
 - `$URL_X` : Regex that applies to the URL
 - `FILE_EXT` : Name of the file uploaded during a multipart POST request


A match zone may be followed by "|NAME". This means that the rule will only apply on the variable's name - and not on the variable's content.
Match zones must be written in lowercase.

Here are some whitelist example rules:

```
BasicRule wl:1000;                              # Disable the rule n°1000. Match zone is empty, so this whitelisting rule will apply everywhere
BasicRule wl:1000 "mz:$ARGS_VAR:foo";           # Disable the rule n°1000 on the GET parameter "foo"
BasicRule wl:1000 "mz:$ARGS_VAR:foo|$URL:/bar"; # Disable the rule n°1000 on the GET parameter "foo", for the URL "/bar"
BasicRule wl:1000 "mz:$URL:/bar|ARGS";          # Disable the rule n°1000 on all GET parameters, for the URL "/bar"
BasicRule wl:1000 "mz:ARGS|NAME";               # Disable the rule n°1000 on all GET parameters
BasicRule wl:1000 "mz:$ARGS_VAR_X:img";         # Disable the rule n°1000 on all GET parameters that contain "img"
BasicRule wl:1000 "mz:$ARGS_VAR_X:^img";        # Disable the rule n°1000 on all GET parameters that begin with "img"
BasicRule wl:1000 "mz:$ARGS_VAR_X:^img_[0-9]+$" # Disable the rule n°1000 on all GET parameters that begin with "img_<and a digit from 0 to 9>"
```

**Threshold definition**

A threshold definition directive has the following format :

```
CheckRule "condition" <Action>
```

Condition is a simple comparison between a score and a constant that defines the maximum accepted score:
 - `$XSS >= 8` checks that the overall "$XSS" counter is not greater that "8". Accepted operators are ">=", ">", "<=" and "<".

Action is triggered when the condition is satisfied:

 - `ALLOW` : Accept the request
 - `LOG` : Log the request
 - `BLOCK` : Block the request (403 forbidden)
 - `DROP` : Log the request during learning mode, and block otherwise

**Logs**

An entry in log files (or elasticsearch / mongodb in Vulture) is added whenever a request breaches a rule.
A Log entry contains details that helps administrators to identify false-positives:

```
<date> [error] <PID>#<TID>: *<connection_id>ip=<client_ip>&server=<server_ip>&uri=<request_uri>&block=<0 or 1>&cscore=<score_name>&score=<score_value>&zone=<zone to inspect>&id=<rule number>&var_name=<name of the variable that contains malicious data>
```

 - `<date>` : The datetime of the request
 - `<PID>`: The apache process ID
 - `<TID>`= The identifier of the execution thread
 - `<connection_id>`: The unique identifier of the connection
 - `ip`: The IP address of the client
 - `server`: The IP address of the server
 - `uri`: The URI of the request
 - `block`: Tells if the request is allowed or blocked
 - `cscore`: The different scores
 - `score`: The different scores values
 - `zone`: The zone in which was the anomaly detected
 - `id`: id of the matched rule
 - `var_name`: Name of the variable that contained the malicious data

 - Extended logs

If this option is enabled in mod_defender engine (see before), then the content of the variables will be logged during learning mode.
This is enabled by default in Vulture when learning mode is enable.

 - JSON logs

Unlike Naxsi, mod_defender allows to natively logs into a JSON Format. This simplifies logs processing by third party tools and uses less storage.


####  Libinjection

libinjection is part of mod_defender. It is a C library that detect SQL and XSS injection.
When enabled, libinjection will act as a blocking rule when an SQL (rule n°17) or XSS (rule n°18) attack is detected. When triggered, LIBINJECTION_SQL or LIBINJECTION_XSS score is incremented by "8".
By default, libinjection is disabled in mod_defender and must be explicitly activated in the configuration file.


#### Internal rules

mod_defender contains a predefined core ruleset :

 - n°2 - `big request` : Request to big (too much data in request)
 - n°10 - `uncommon hex encoding` : Encoding of the request is likely to be related to an attack
 - n°11 - `uncommon content-type` : The content-type of the request is unknown or not supported
 - n°12 - `uncommon URL` : The URL is malformed
 - n°13 - `uncommon post format` : The disposition of parameters within the request is not correct
 - n°14 - `uncommon post boundary` : Boundaries between request parameters are malformed
 - n°15 - `invalid JSON` : JSON contained in the request body is malformed
 - n°16 - `Empty post body` : The POST request has an empty BODY
 - n°17 - `Libinjection SQL` : Libinjection SQL detects an SQL injection attempt
 - n°18 - `Libinjection XSS` : Libinjection XSS detects an Cross Site Scripting attempt

mod_defender comes by default with the same "main rules" as Naxsi's one. These rules must always been enabled.
They are ordered as the following :

 - n°1000 à 1099 : Rules related to SQL injection
 - n°1100 à 1199 : Rules related to remote file inclusion (RFI)
 - n°1200 à 1299 : Rules related to attack on path (Directory Traversal)
 - n°1300 à 1399 : Rules related to XSS attacks
 - n°1400 à 1499 : Rules related to XSS filter evasion
 - n°1500 à 1599 : Rules related to file upload

#### NXApi/NXTool

NXApi is a tool developed by NBS System. This tool performs the following task :

 - Read mod_defender logfiles on disk and send logs in elasticsearch (this is useless in Vulture, because mod_defender learning logs are natively send to elasticsearch / mongodb since GUI-1.44).
 - Automaticaly Build whitelist (basic rules) after analysis of learning logs. This is done with a statistical approach.
 - Allow the admin to select log entries that need to be ignored or taken into account when generating whitelists
 - Display informations about imported learning logs


As a best practice, it is recommanded to enable learning mode during a test phase on a given application.
This ensures that no attacks will be recorded and so it limits the amount of work needed to eliminate false-negative (whitelisting of an attack).


### Unit testing and benchmark of mod_defender

In order to test mod_defender, we write up a bash script, to test every main rules:

![WAF-FIG-1](/doc/img/waf-fig-1.png)

**Requests flow**

When mod_defender enters into production mode, it scores every request. Depending of the whitelist basic rules, the request may be accepted or rejected.
The following figure shows how each request is processed by mod_defender. First, it is inspected to detect the presence of dangerous characters and SQL keywords. Then, the score is computed and verified against the maximum score threshold.
Depending of the resulting score, the request if allowed or rejected (HTTP 403 - FORBIDDEN):

![WAF-FIG-2](/doc/img/waf-fig-2.png)


**Whitelist and basic rules**

As stated before, mod_defender uses a default blacklist (main rules). However, whitelists are more extensible / configurable and should be created for every app to protect.
At startup, mod_defender builds up to 4 hash tables, one for each zone:


![WAF-FIG-3](/doc/img/waf-fig-3.png)

 - ARGS contains GET parameters
 - URL contains the URL of the requested resource
 - BODY contains POST parameters
 - HEADER contains incoming HTTP headers


As before, once a request is allowed, it is processed and divided into 4 parts: one for each zone (ARGS, URL, BODY, HEADERS). Each table has a variable number of elements and is processed separately. Every parameter is inspected to detect the presence of suspicious part. Moreover, the current parameter is looked for in the corresponding hash table of the zone in order to find if it is whitelisted or not. If no whitelist rule is found, the score of the main rule is applied.
Once all parts have been processed, a global verification of SQL, RFI, TRAVERSAL and XSS score is performed to check if they are below the maximum accepted threshold.

![WAF-FIG-4](/doc/img/waf-fig-4.png)
This approach shows that rules are processed in an efficient manner. By creating hash tables with whitelist, the search phase is done in a constant time. Moreover, since the request is divided into 4 parts, parameter processing is done separately.
This permit to consult hash tables only when needed. For instance, if a request contains several parameter in its URL, but only one is suspicious, each parameter is compared to the main rules (blacklist), but only the suspicious one will be analyzed later.


##Testing protocol

This section describes the method and tools used to measure mod_defender's performances.

###Testing platform

![WAF-FIG-5](/doc/img/waf-fig-5.png)

Hosts are connected to the same LAN segment on a dedicated Ethernet switch.
The test host (192.168.0.1) represents a Web user, external to the architecture. Performance tools are installed on this host.

The reverse-proxy host (192.168.0.1) filters traffic between the test machine and the Web backend.
A first series of test has been performed with **Apache + mod_defender** then with **Apache + mod_security**, then with **nginx + naxsi**

Used versions are:

 - Apache 2.4.25 mpm_worker with mod_proxy, mod_proxy_http, mod_defender / mod_security
 - Nginx 1.13 with Naxsi 0.55.3.

WAF has been configured with almost identical policies and ruleset.
Apache configuration is :
```
<VirtualHost *:80>
    ProxyPreserveHost On
    ProxyRequests On
    ProxyPass / http://192.168.0.3/
    ProxyPassReverse / http://192.168.0.3/
</VirtualHost>
```

Access Log are disabled in order to have the maximum performance (no disk i/o).

The Web backend (192.168.0.3) is a classical LAMP server with phpBB.
Tests have been made
 1. Without the PHP stack (the backend immediately returns 200 - OK)
 2. With the PHP stack (access to phpBB forum)

The Web backend is twice as much performant (CPU and RAM) than the reverse-proxy host, so that we can be sure that the limiting component is the reverse-proxy and not the web backend.


###Benchmark and performance measurement

**Apache Bench**
We use a perl script to increase the number of parameters in the URL and also to compute the average number of requests per second that the reverse-proxy is able to deal with.


**Httperf/Autobench**

We used autobench to compute the maximum number of simultaneous connexions that the reverse-proxy can handle.

Requests against phpBB with no forbidden parameters:

![WAF-FIG-6](/doc/img/waf-fig-6.png)

Requests against phpBB with forbidden parameters (web attacks):

![WAF-FIG-7](/doc/img/waf-fig-7.png)

Requests against the "200 - OK" backend with no forbidden parameters :

![WAF-FIG-8](/doc/img/waf-fig-8.png)

Requests against the "200 - OK" backend with forbidden parameters (web attacks):

![WAF-FIG-9](/doc/img/waf-fig-9.png)
