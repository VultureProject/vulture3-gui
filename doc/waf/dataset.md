---
title: "Machine learning Dataset"
currentMenu: dataset
parentMenu: waf
---

This menu lists previously built datasets.<br/>

## SVM
You will see be able to know the `name`, the `number of lines`, the time when it was generated, and for what reason it is being used.

`name`: The name of the dataset, which is the name of the targeted application followed by the creation dat.e<br/>
`Number of lines`: Number of log line of the dataset, we recommend at least 1000 lines to have good results.<br/>
`Built`: This field become "True" once the dataset has finished to be imported from the log interface.<br/>
`SVM`: This field become "True" once the SVM is built.<br/>
`Actions`: The buttons allowing to organise the anomaly detection module.<br/>
`Preview`: Let you view the multiple detection graphs, only avaible once the SVM are built.<br/>
`Build`: Let you construct the SVM allowing you to determine the learning bounds and thus then detects anomalies. Before launching the construction, you must select the precision parameters of all the algorithms, this one is by default selected to 1/n (n being the number of log lines). We recommend to adjust this parameter in function of the obtained results while previewing with graphs.<br/>
`Edit the dataset`: Let you preview your dataset and delete log lines.<br/>
`Delete dataset`: Delete the dataset and associated SVM.<br/>

## Learning

When you enable learning mode, you will see learning datasets, listed after SVM one's.
They are named following this pattern: &lt;name of app in learning mode&gt;-defender-whitelist

If you think that you have "learned" enough of the web traffic of your backend and wish to generate all the whitelists automatically,
you can just click the flash logo.

You can browse the learning set by clicking on the logo looking like table lines,
this will let you browse the learning set line by line,
from this view, you can see in red the lines that are not whitelisted and in the green the one's who are,
you can click on a line and it will bring you a selection of possible whitelists
for patterns detected in each variables or variable name's,
on the very right, you can tick the whitelists that you want to use,
on the right side, you have an human readable description of what it does,
and on the left side, you have the corresponding directive,
be careful, some whitelists are more permissive than other.

Generated whitelists rulesets appear in [WAF Ruleset](ruleset.html), they are named with the following pattern:
 learning\_&lt;app name&gt;\_&lt;app id&gt; WL.
Inside, whitelist rules are unique.

And finally you can delete the learning set by clicking on the trash icon.
