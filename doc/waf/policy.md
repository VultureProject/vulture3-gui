---
title: "WAF Policy"
currentMenu: policy
parentMenu: waf
---

This menu lists the custom policies in effect by mod_security.

It allows you to create new one on the fly, and you can fine tune them.

## Main settings
`Fiendly name`: The name of the policy.<br/> <br>

`Enable body inspection`: Toggle the body parsing (CPU intensive).<br/>
This option will enable or disable the <b>SecRequestBodyAccess</b> ModSecurity directive. <br>
This directive is required if you use a RuleSet like OWASP-RS or Vulture-RS in your application. <br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecRequestBodyAccess for more informations about this option.

`Enable content injection`: Toggle the content injection (CPU intensive)<br/>
This option will enable or disable the <b>SecContentInjection</b> and <b>SecStreamOutBodyInspection</b> ModSecurity directives. <br>
This option is required if you use a RuleSet like OWASP-RS or Vulture-RS in your application. <br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecRequestBodyAccess and https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecStreamOutBodyInspection for more information about this option.

`Disable backend compression`: Disable compression.<br/>
This option will enable or disable the <b>SecDisableBackendCompression</b> ModSecurity directive. <br>
That one is required if you have "body inspection" and/or "content injection" enabled, as well as to use OWASP-RS or Vulture-RS. <br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecDisableBackendCompression for more information about this option. <br> <br>

`Validate UTF8 Encoding`: Toggle the parsing and validation of the UTF8 encoding compliance. <br/>
Enable that option will set the ModSecurity variable "tx.crs_validate_utf8_encoding=1".<br>
You have to use the OWASP-RS in your application to enable this option. <br><br>

`XML Inspection`: Validate the XML structure correctness. <br/>
Enable that option will set the ModSecurity variable "tx.requestBodyProcessor=XML".<br>
You have to use the OWASP-RS in your application to enable this option. <br><br>

`Block invalid body`: Returns 400 (Invalid request) status code is body is detected as invalid. <br/>
This option enable the following ModSecurity directive: <br>
SecRule REQBODY_ERROR "@eq 1" \
        "id:'95',phase:2,t:none,log,deny,status:400,msg:'Failed to parse request body.',logdata:'%{reqbody_error_msg}',severity:2" <br>
The REQBODY_ERROR variable is set in the OWASP Core Rules Set, so you have to use the OWASP-RS in your application to verify the body correctness. <br><br>

`Connections engine`: Toggle the rule, or set it up as detection only to log only.<br/>
This option will modify the <b>SecConnEngine</b> ModSecurity directive. <br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecConnEngine for more information about this option. <br> <br>

`Audit Engine`: Log level, enable/disable or only log if revelant.<br/>
This option will modify the <b>SecAuditEngine</b> ModSecurity directive. <br>
This directive is used to configure the audit engine, which logs complete transactions. <br>
Three options are available :
* On : log all transactions,
* Off, do not log any transaction,
* RelevantOnly: only the log transactions that have triggered a warning or an error, or have a status code that is considered to be relevant (as determined by the SecAuditLogRelevantStatus directive).<br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecAuditEngine for more informations about this option. <br> <br>

`Relevant status code`: This option is used if the last option is configured with the value "RelevantOnly". <br>
It will set the <b>SecAuditLogRelevantStatus</b> directive. <br>
The default regex "^(?:5|4(?!04))" means that all 4xx and 5xx status code will be logged, except for 404s. <br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecAuditLogRelevantStatus for more informations about this option. <br> <br>

`Logging Mode`: Select the log file, audit_log, error_log or both<br/>
This option will modify the <b>SecDefaultAction</b> ModSecurity directive. <br>
Three options are available : <br>
Both, this will set the directive with the value : SecDefaultAction "phase:2,pass,log"<br>
Audit logs, this will set the directive with the value : SecDefaultAction "phase:2,pass,nolog,auditlog"<br>
Apache error logs, this will set the directive with the value : SecDefaultAction "phase:2,pass,log,noauditlog"<br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecDefaultAction for more informations about this option. <br> <br>

`Enable Mod Defender`: Toggle the activation of Mod Defender.<br/>
This option will enable or disable the <b>Defender</b> ModDefender directive. <br>
This directive is required if you want to use : <br>
* Generic SQL detection
* Generic XSS detection
See https://www.vultureproject.org/doc/waf/waf.html for more informations about Mod Defender in Vulture. <br> <br>

`Enable Generic SQL Detection`: Toggle the activation of LibinjectionSQL.<br/>
This option will enable or disable the <b>LibinjectionSQL</b> ModDefender directive. <br>
That directive will activate the use of the <b>libinjection</b> library. <br>
The last option must be enabled to use that one. <br>
See https://www.vultureproject.org/doc/waf/waf.html for more informations about libinjection. <br> <br>

`Enable Generic XSS Detection`: Toggle the activation of LibinjectionXSS.<br/>
This option will enable or disable the <b>LibinjectionXSS</b> ModDefender directive. <br>
That directive will activate the use of the <b>libinjection</b> library. <br>
The "Enable Mod Defender" option must be enabled to use that one. <br>
See https://www.vultureproject.org/doc/waf/waf.html for more informations about libinjection. <br> <br>


## Scoring
Each HTTP request begins with an anomaly score of 0 and is incremented each time a rule match.<br/>
If a threshold (inbound or outbound) is reaches, corresponding actions are triggered.<br/>
`Security Level`: Increase or decrease the anomal score threshold depending on the security level. <br>
`Block desktop users User-Agent`: Enable this toggle will set the variable "ua_browser_anomaly_score" to 999, which means that if the user-agent is detected as "Desktop user", the anomaly score will be increased by 999, and reach the threshold an block the request. <br>
`Block crawlers User-Agent`: Enable this toggle will set the variable "ua_crawler_anomaly_score" to 999, which means that if the user-agent is detected as "Desktop user", the anomaly score will be increased by 999, and reach the threshold and block the request. <br>
If this toggle is not enabled, the anomaly score will be incremented by 2 in case of detecting the User-Agent as a crawler. <br>
`Block suspicious User-Agent`: Enable this toggle will set the following variable to 999:  <br>
ua_unknown_anomaly_score, ua_anonymous_anomaly_score, ua_bot_anomaly_score, ua_console_anomaly_score, ua_emailclient_anomaly_score, ua_emailharvester_anomaly_score, ua_script_anomaly_score <br>
which means that if the user-agent is detected as "Unknown" or "Anonymous" or "Bot" or "Console" or "emailclient" or "emailharvester" or "script", the anomaly score will be increased by 999, and reach the threshold and block the request. <br>
If this toggle is not enabled, the scores will be set to 2 by default. <br>

`Critical anomaly score`: The score added to the anomaly score when a critical rule match.<br/>
`Error anomaly score`: The score added to the anomaly score when an error rule match.<br/>
`Warning anomaly score`: The score added to the anomaly score when a warning rule match<.br/>
`Notice anomaly score`: The score added to the anomaly score when a notice rule match.<br/>
`Block if global score exceeds`: The score threshold that when reached will block the request.<br/>

## HTTP Policy
`Maximum number of arguments in request`: The maximum number of parameters in the request.<br/>
This value will be set by the following ModSecurity directives : <br>
    SecAction "id:'6', phase:2, t:none, setvar:tx.max_num_args={{policy.max_num_args}}, nolog, pass" <br>
This 2 variables will be used by the OWASP Rules Set, more precisely by the file <b>modsecurity_crs_23_request_limits.conf</b>.<br>
You need to enable the OWASP-RS in your application to block the request if that value is reached. <br><br>

`Maximum argument name length`: The maximum name length for each request parameters.<br/>
This value will be set by the following ModSecurity directive: <br>
    SecAction "id:'7', phase:2, t:none, setvar:tx.arg_name_length={{policy.arg_name_length}}, nolog, pass" <br>
This 2 variables will be used by the OWASP Rules Set, more precisely by the file <b>modsecurity_crs_23_request_limits.conf</b>.<br>
You need to enable the OWASP-RS in your application to block the request if that value is reached. <br><br>

`Maximum arguments value length`: The maximum value length for each request parameters. <br/>
This value will be set by the following ModSecurity directive: <br>
    SecAction "id:'8', phase:2, t:none, setvar:tx.arg_length={{policy.arg_length}}, nolog, pass"
This variable will be used by the OWASP Rules Set, more precisely by the file <b>modsecurity_crs_23_request_limits.conf</b>.<br>
You need to enable the OWASP-RS in your application to block the request if that value is reached. <br><br>

`Maximum arguments value total length`: The request arguments total length. <br/>
This value will be set by the following ModSecurity directive: <br>
    SecAction "id:'9', phase:2, t:none, setvar:tx.total_arg_length={{policy.total_arg_length}}, nolog, pass"
This variable will be used by the OWASP Rules Set, more precisely by the file <b>modsecurity_crs_23_request_limits.conf</b>.<br>
You need to enable the OWASP-RS in your application to block the request if that value is reached. <br><br>

`Request body limit`: The request body length limit. <br/>
This value will be set by the following ModSecurity directive: <br>
    SecRequestBodyNoFilesLimit {{policy.request_body_limit}}
And by the following ModDefender directive: <br>
    RequestBodyLimit {{ policy.request_body_limit }}
If this variable is reached, ModDefender will send a 403 HTTP code response, and if ModDefender is disable, ModSecurity will send a 413 (Request entity too large) HTTP code response.<br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecRequestBodyNoFilesLimit for more informations about the ModSecurity directive, <br>
 and see https://www.vultureproject.org/doc/waf/waf.html for more informations about ModDefender directive. <br><br>

`Maximum file size, in bytes`: The maximum files size allowed to upload. <br/>
This value will be set by the following ModSecurity directive: <br>
    SecRequestBodyLimit {{policy.max_file_size}}
If this variable is reached by the "Content-Length" header value, ModSecurity will send a 413 (Request entity too large) HTTP code response.<br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecRequestBodyLimit for more informations about the ModSecurity directive. <br>

`Maximum combined file size, in bytes`: The maximum file size allowed to upload. <br/>
This value will be set by the following ModSecurity directive: <br>
    SecAction "id:'11', phase:2, t:none, setvar:tx.combined_file_sizes={{policy.combined_file_sizes}}, nolog, pass" <br>
And will be, in the OWASP Core Rules Set, compared to the ModSecurity variable "FILES_COMBINED_SIZE". If that value is reached, the anomaly score will be incremented by the "critical_anomaly_score" value. <br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#FILES_COMBINED_SIZE for more information about that ModSecurity macro. <br><br>

`Allowed HTTP versions`: Allowed HTTP protocol versions. <br/>
This value will be set by the following ModSecurity directive: <br>
    setvar:tx.allowed_http_versions={{policy.allowed_http_versions}} <br>
If a non allowed method is detected, the anomaly score will be incremented by the "warning anomaly score" value by the OWASP-RS, more precisely in the file <b>REQUEST-920-PROTOCOL-ENFORCEMENT.conf</b><br>
and incremented by the "critical anomaly score" value by the Vulture-RS. <br><br>

`Allowed request content type`: Allowed Content-Type headers. <br/>
This value will be set by the following ModSecurity directive:
    setvar:tx.allowed_request_content_type={{policy.allowed_request_content_type}}
If a non allowed Content-Type header is detected, the anomaly score will be incremented by the "warning anomaly score" value by the OWASP-RS, more precisely in the file <b>REQUEST-920-PROTOCOL-ENFORCEMENT.conf</b><br>
and incremented by the "critical anomaly score" by the Vulture-RS.<br><br>

`Restricted extensions`: The file extension allowed for requested files. <br/>
This value will be set by the following ModSecurity directive:
    setvar:tx.restricted_extensions={{policy.restricted_extensions}}
If a non allowed requested file extension is detected, the anomaly score will be incremented by the "critical anomaly score" value by the OWASP-RS, more precisely in the file <b>REQUEST-920-PROTOCOL-ENFORCEMENT.conf</b><br>
and incremented by the "critical anomaly score" by the Vulture-RS.<br><br>


`Restricted headers`: Restricted (allowed) headers name.<br/>
This value will be set by the following ModSecurity directive:
    setvar:tx.restricted_headers={{policy.restricted_headers}}
If a non allowed header name is detected, the anomaly score will be incremented by the "critical anomaly score" value by the OWASP-RS, more precisely in the file <b>REQUEST-920-PROTOCOL-ENFORCEMENT.conf</b><br>
and incremented by the "critical anomaly score" by the Vulture-RS.<br><br>

## DOS & BF Protection
You can here define an anti DOS policy by specifying the protected urls (or all), the burst time period, the threshold and the block timeout.<br/>
The first rule is a default protection for all the URLs. <br>
If a client request the specified URL more than "DOS Counter threshold" times within a period of "DOS Burst Time Slice" seconds, he will be blocked for a period of "DOS Block Timeout" seconds.

    Since version 1.63 you can enable/disable the global rule.

Those rules will be defined by the following ModSecurity directives, one per DOS Rule:
    SecAction "id:'', phase:2, t:none, setvar:'tx.brute_force_protected_urls={{dos_rule.url}}', setvar:'tx.brute_force_burst_time_slice={{dos_rule.burst_time_slice}}', setvar:'tx.brute_force_counter_threshold={{dos_rule.counter_threshold}}', setvar:'tx.brute_force_block_timeout={{dos_rule.block_timeout}}', auditlog, pass"
These directives will be then checked by the following custom ModSecurity directives:
    SecRule IP:BRUTE_FORCE_BLOCK "@eq 1" "chain,phase:3,id:'236',deny,status:403,msg:'Brute Force Attack Identified from %{tx.real_ip} (%{tx.brute_force_block_counter} hits since last alert)',setvar:ip.dos_block_counter=+1"
    SecRule &IP:BRUTE_FORCE_BLOCK_FLAG "@eq 0" "setvar:ip.dos_block_flag=1,expirevar:ip.dos_block_flag=60,setvar:tx.brute_force_block_counter=%{ip.dos_block_counter},setvar:ip.dos_block_counter=0"
    # Block and track # of requests but don't log
    SecRule IP:BRUTE_FORCE_BLOCK "@eq 1" "phase:3,id:'237',deny,status:403,auditlog,setvar:ip.dos_block_counter=+1"
    SecRule &TX:BRUTE_FORCE_PROTECTED_URLS "@eq 0" "phase:5,id:'238',t:none,nolog,pass,skipAfter:END_BRUTE_FORCE_PROTECTION_CHECKS"
    SecRule REQUEST_FILENAME "!@within %{tx.brute_force_protected_urls}" "phase:5,id:'239',t:none,nolog,pass,skipAfter:END_BRUTE_FORCE_PROTECTION_CHECKS"
    SecRule IP:BRUTE_FORCE_BLOCK "@eq 1" "phase:5,id:'240',t:none,nolog,pass,skipAfter:END_BRUTE_FORCE_PROTECTION_CHECKS"
    SecAction "phase:5,id:'241',t:none,auditlog,pass,setvar:ip.dos_counter=+1"
    SecRule IP:BRUTE_FORCE_COUNTER "@gt %{tx.brute_force_counter_threshold}" "phase:5,id:'242',t:none,auditlog,pass,t:none,setvar:ip.dos_burst_counter=+1,expirevar:ip.dos_burst_counter=%{tx.brute_force_burst_time_slice},setvar:!ip.dos_counter"
    SecAction "phase:5,id:'13',auditlog,msg:'%{ip.dos_counter}'"
    SecRule IP:BRUTE_FORCE_BURST_COUNTER "@ge 2" "phase:5,id:'243',t:none,log,pass,msg:'Potential Brute Force Attack from %{tx.real_ip} - # of Request Bursts: %{ip.dos_burst_counter}',setvar:ip.dos_block=1,expirevar:ip.dos_block=%{tx.brute_force_block_timeout}"
    SecMarker END_BRUTE_FORCE_PROTECTION_CHECKS
Feel free to contact us if you have any improvement relative to these rules. <br><br>

## Advanced
`Arguments separator in forms`: Specify which character to use as argument separator.<br/>
This value will be set by the following ModSecurity directive: <br>
    <b>SecArgumentSeparator</b> <br>
This option is used for application/x-www-form- urlencoded content. <br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecArgumentSeparator for any information about this directive.<br><br>

`Collections Timeout`: Specify the collection timeout, default is 3600 seconds.<br/>
For each client identified by client-ip/user-agent, a collection is created and maintained in Redis. In case of a client does not contact the server for a timeout, the collection is deleted. <br>
You can change that value to delete the collections after another timeout. <br>
That value is set by the following ModSecurity directive : <b>SecCollectionTimeout</b>. <br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecCollectionTimeout for more informations about this option. <br><br>

`Cookie Format`: The cookie format, either version 0 (netscape) or version 1 (value can be token or quoted string).<br/>
That value will be set by the following ModSecurity directive: <b>SecCookieFormat</b>. <br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecCookieFormat for more informations about this option. <br><br>

`Cookie Separator`: The defined cookie seperator. <br/>
Specifies which character to use as the separator for cookie v0 content. <br>
That value will be set by the following ModSecurity directive : <b>SecCookieV0Separator</b>. <br>
See https://github.com/SpiderLabs/ModSecurity/wiki/Reference-Manual#SecCookieV0Separator for more informations about this option. <br><br>

## Custom directives
Here you can add raw mod_security directives.<br/>
This block will be directly past in the <Proxy> section of the application which use that Policy. <br>
