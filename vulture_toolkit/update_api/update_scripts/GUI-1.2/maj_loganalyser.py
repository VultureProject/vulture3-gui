#!/home/vlt-gui/env/bin/python2.7
# coding:utf-8

"""This file is part of Vulture 3.

Vulture 3 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Vulture 3 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vulture 3.  If not, see http://www.gnu.org/licenses/.
"""
__author__     = "Olivier de Régis"
__credits__    = []
__license__    = "GPLv3"
__version__    = "3.0.0"
__maintainer__ = "Vulture Project"
__email__      = "contact@vultureproject.org"
__doc__        = """This migration script update database for 
logging into the MongoDB Internal Repository"""

import os
import sys

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'vulture.settings')

import django
django.setup()

from gui.models.system_settings import Cluster, LogAnalyserSettings, LogAnalyserRules

cluster = Cluster.objects.get()
cluster.system_settings.loganalyser_settings = LogAnalyserSettings()
cluster.system_settings.loganalyser_settings.loganalyser_rules = []
cluster.save()

LOGANALYSER_DATABASES = [
    #("http ://www.projectdsfshoneypot.org/list_of_ips.php?t=d&rss=1", "Project Honey Pot Directory of Dictionary Attacker IPs"),
    ("https://check.torproject.org/cgi-bin/TorBulkExitList.py?ip=1.1.1.1", ["tor"], "TOR Exit Nodes"),
    ("https://www.maxmind.com/en/proxy-detection-sample-list", ["proxy"], "MaxMind GeoIP Anonymous Proxies"),
    ("http://danger.rulez.sk/projects/bruteforceblocker/blist.php", ["spammer"], "BruteForceBlocker IP List"),
    ("https://www.spamhaus.org/drop/drop.lasso", ["spammer"], "Spamhaus Don't Route Or Peer List (DROP)"),
    ("http://cinsscore.com/list/ci-badguys.txt", ["suspicious"], "C.I. Army Malicious IP List"),
    ("https://www.openbl.org/lists/base.txt", ["abuse"], "OpenBL.org 30 day List"),
    ("https://www.autoshun.org/files/shunlist.csv", ["attacker"], "Autoshun Shun List"),
    ("https://lists.blocklist.de/lists/all.txt", ["attacker"], "blocklist.de attackers"),
    ("https://www.stopforumspam.com/downloads/toxic_ip_cidr.txt", ["spammer"], "StopForumSpam"),
    ("http://blocklist.greensnow.co/greensnow.txt", ["bruteforce"], "GreenSnow"),
    ("https://reputation.alienvault.com/reputation.generic", ["bad_reputation"], "alienvault.com - ip bad reputation"),
    ("https://www.badips.com/get/list/any/2?age=7d", ["bad_reputation"], "badips.com - ip bad reputation"),
    ("https://www.autoshun.org/files/shunlist.csv", ["attacker"], "autoshun.org - Shunlist"),
    ("http://osint.bambenekconsulting.com/feeds/c2-ipmasterlist.txt", ["suspicious"], "bambenekconsulting.com - ip master"),
    ##("http://osint.bambenekconsulting.com/feeds/dga-feed.txt", ["spammer"], "bambenekconsulting.com - dga (malware)"),
    ("http://www.binarydefense.com/banlist.txt", ["suspicious"], "binarydefense.com - malicious"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/bitcoin_nodes_1d.ipset", ["bitcoin"], "bitnodes.io - Bad reputation (bitcoin node)"),
    ("http://lists.blocklist.de/lists/all.txt", ["attacker"], "blocklist.de - Attackers"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/botscout_1d.ipset", ["spammer"], "botscout.com - Spammer"),
    ("http://danger.rulez.sk/projects/bruteforceblocker/blist.php", ["attacker"], "rulez.sk - Brute force (attacker)"),
    ("http://cinsscore.com/list/ci-badguys.txt", ["attacker"], "cinsscore.com - Attacker"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/cruzit_web_attacks.ipset", ["attacker"], "cruzit.com - Attacker"),
    ("http://cybercrime-tracker.net/all.php", ["malware"], "cybercrime-tracker.net - Malware"),
    ("https://intel.deepviz.com/recap_network.php?tw=7d&active=network_domains", ["botnet"], "deepviz.com - Deepviz Threat Intel"),
    ##("http://www.dshield.org/feeds/suspiciousdomains_High.txt", "dshield.org - Suspicious domain"),
    ("http://feeds.dshield.org/top10-2.txt", ["attacker"], "dshield.org - Top attacker"),
    ("http://rules.emergingthreats.net/open/suricata/rules/botcc.rules", ["malware"], "emergingthreats.net - Malware"),
    ("http://rules.emergingthreats.net/open/suricata/rules/compromised-ips.txt", ["suspicious"], "emergingthreats.net - Compromised host (suspicious)"),
    ("https://rules.emergingthreats.net/open/suricata/rules/emerging-dns.rules", ["malware"], "emergingthreats.net - Malware"),
    #("https://feodotracker.abuse.ch/blocklist/?download=domainblocklist", "abuse.ch - Feodo (malware)"),
    ("https://feodotracker.abuse.ch/blocklist/?download=ipblocklist", ["malware"], "abuse.ch - Feodo (malware)"),
    ("http://blocklist.greensnow.co/greensnow.txt", ["attacker"], "greensnow.co - Attacker"),
    ##("https://raw.githubusercontent.com/Neo23x0/Loki/master/iocs/otx-c2-iocs.txt", "otx.alienvault.com - Malware"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/malc0de.ipset", ["malware"], "malc0de.com - Malware distribution (suspicious)"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/malwaredomainlist.ipset", ["malware"], "malwaredomainlist.com - Malware"),
    ##("http://malwaredomains.lehigh.edu/files/domains.txt", "malwaredomains.com - Malware"),
    ("https://lists.malwarepatrol.net/cgi/getfile?receipt=f1417692233&product=8&list=dansguardian", ["malware"], "malwarepatrol.net - Malware Patrol"),
    ("https://www.maxmind.com/en/proxy-detection-sample-list", ["proxy", "suspicious"], "maxmind.com - Anonymous proxy (suspicious)"),
    ("https://myip.ms/files/blacklist/htaccess/latest_blacklist.txt", ["crawler"], "myip.ms - Crawler"),
    ("http://www.nothink.org/blacklist/blacklist_malware_irc.txt", ["malware"], "nothink.org - Malware IRC"),
    ("http://www.openbl.org/lists/base.txt", ["attacker"], "openbl.org - Attacker"),
    ("https://openphish.com/feed.txt", ["phishing"], "openphish.com - Phishing"),
    ("https://palevotracker.abuse.ch/blocklists.php?download=combinedblocklist", ["malware"], "abuse.ch - Palevo (malware)"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/proxylists_1d.ipset", ["proxy", "suspicious"], "proxylists.net - Proxy (suspicious)"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/proxyrss_1d.ipset", ["proxy", "suspicious"], "proxyrss.com - Proxy (suspicious)"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/proxyspy_1d.ipset", ["proxy", "suspicious"], "spys.ru - Proxy (suspicious)"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/ri_web_proxies_30d.ipset", ["proxy", "suspicious"], "rosinstrument.com - Proxy (suspicious)"),
    ("http://report.rutgers.edu/DROP/attackers", ["attacker"], "rutgers.edu - Attacker"),
    ("http://sblam.com/blacklist.txt", ["spammer"], "sblam.com - Http spammer"),
    ("http://labs.snort.org/feeds/ip-filter.blf", ["attacker"], "snort.org - Attacker"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/socks_proxy_7d.ipset", ["proxy", "suspicious"], "socks-proxy.net - Proxy (suspicious)"),
    ("https://sslbl.abuse.ch/blacklist/sslipblacklist.csv", ["abuse"], "abuse.ch - SSL IPBL"),
    ("https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/sslproxies_1d.ipset", ["proxy", "suspicious"], "sslproxies.org - Proxy (suspicious)"),
    ("https://check.torproject.org/cgi-bin/TorBulkExitList.py?ip=1.1.1.1", ["proxy", "suspicious"], "torproject.org - Tor exit node (suspicious)"),
    ("https://torstatus.blutmagie.de/ip_list_all.php/Tor_ip_list_ALL.csv", ["proxy", "suspicious"], "blutmagie.de - Tor exit node (suspicious)"),
    ("http://www.voipbl.org/update/", ["attacker"], "voipbl.org - Attacker"),
    ("http://vxvault.net/URL_List.php", ["malware"], "vxvault.net - Malware"),
    ##("https://zeustracker.abuse.ch/blocklist.php?download=domainblocklist", ["spammer"], "abuse.ch - Zeus (malware)"),
    ("https://zeustracker.abuse.ch/blocklist.php?download=badips", ["malware", "zeus"], "abuse.ch - Zeus (malware)"),
    ("https://zeustracker.abuse.ch/monitor.php?filter=all", ["malware", "zeus"], "abuse.ch - Zeus Tracker"),
    ("https://zeustracker.abuse.ch/blocklist.php?download=compromised", ["malware", "zeus"], "abuse.ch - Zeus (malware)"),
]

for rule in LOGANALYSER_DATABASES:
    cluster.system_settings.loganalyser_settings.loganalyser_rules.append(LogAnalyserRules(**{
        'url': rule[0],
        'description': rule[2],
        'tags': ",".join(rule[1])
    }))

cluster.save()