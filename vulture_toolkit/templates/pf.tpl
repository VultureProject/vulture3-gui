rule=:%hostname:word% %time:word% rule %rule:number%/0(match): %action:word% %direction:alpha% on %interface:char-to:\x3a%: %src_ip:ipv4%.%src_port:number% > %dst_ip:ipv4%.%dst_port:number%: %info:rest%
rule=:%hostname:word% %time:word% rule %rule:number%/0(match): %action:word% %direction:alpha% on %interface:char-to:\x3a%: %src_ip:ipv6%.%src_port:number% > %dst_ip:ipv6%.%dst_port:number%: %info:rest%
rule=:%hostname:word% %time:word% rule %rule:number%/0(match): %action:word% %direction:alpha% on %interface:char-to:\x3a%: %src_ip:ipv4% > %dst_ip:ipv4%: %info:rest%
rule=:%hostname:word% %time:word% rule %rule:number%/0(match): %action:word% %direction:alpha% on %interface:char-to:\x3a%: %src_ip:ipv6% > %dst_ip:ipv6%: %info:rest%
