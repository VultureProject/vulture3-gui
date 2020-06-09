---
title: "Reports"
currentMenu: report
parentMenu: waf
---

In this interface, you can preview the learning bounds linked to you learning dataset. The bounds delimit area considered as legitimate.

6 algorithms are available:
`Data received by server`: Correlates the quantity if received response by the server and the HTTP status code.
`Data sent by user`: Correlates the quantity of data sent by the client and the HTTP status code.
`Traffic evolution over day per IP`: Correlates the number of request per second per unique IP according to the time of the day.
`Request content analysis`: Analyzes the content of the request and compares it with the learning dataset to correlate the "distance" between words. Two sub algorithms are available, the first one analyze the whole request, the second split character by "/".

Once the real time button is ticked, the real time generated traffic on the application is analyzed and synchonized on the graphs.
This let you check if the learning model works. If the analysis results are not compliant with reality, you have the ability to generate the model with different parameters.
The traffic flagged as legitimate is represented as squares and the anomalies as dots.
