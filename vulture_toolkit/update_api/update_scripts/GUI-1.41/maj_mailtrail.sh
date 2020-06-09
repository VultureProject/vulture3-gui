#!/bin/sh
#
# This script write the maltrail crontab script and updates execution right for crontab of vlt-gui
#
#


/bin/echo "#!/home/vlt-gui/env/bin/python
#-*- coding: utf-8 -*-
\"\"\"This file is part of Vulture 3.

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
\"\"\"
__author__     = \"Olivier de Régis\"
__credits__    = []
__license__    = \"GPLv3\"
__version__    = \"3.0.0\"
__maintainer__ = \"Vulture Project\"
__email__      = \"contact@vultureproject.org\"
__doc__        = \"Update maltrail reputation IP list\"


import sys
import os

# Django setup part
sys.path.append(\"/home/vlt-gui/vulture/\")
os.environ.setdefault(\"DJANGO_SETTINGS_MODULE\", \"vulture.settings\")

import django
django.setup()

import requests
import redis
import time
import re

from gui.models.system_settings import Cluster


class Maltrail:
    def __str__(self):
        return \"ctx_tags\"

    def __init__(self):
        self.maltrail_path_file     = \"/var/db/loganalyzer/maltrail.csv\"
        self.maltrail_ip_list       = []
        self.maltrail_ip_list_mongo = Cluster.objects.get().system_settings.loganalyser_settings.loganalyser_rules
        
        for database in self.maltrail_ip_list_mongo:
            self.maltrail_ip_list.append([database[\"url\"], database[\"tags\"].split(\",\"), database[\"description\"]])

        self.redis_cli = redis.StrictRedis(unix_socket_path=\"/var/db/redis/redis.sock\", db=0)

    def fetch(self):
        total_count = 0
        data        = {}

        headers = {
            \"User-Agent\": \"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36\"}

        for database in self.maltrail_ip_list:
            try:
                count = 0
                req = requests.get(database[0], stream=True, headers=headers, proxies=self.__get_proxy_conf())

                for line in req.iter_lines():
                    for ip in re.findall(r\"[0-9]+(?:\.[0-9]+){3}\", line):
                        data.setdefault(ip, set()).update(database[1])
                        count += 1
                print(\"%6s  %s\" % (count, database[2]))
                total_count += count
            except Exception, e:
                raise
                print(\"error : \", database[2])

        print(\"TOTAL IP COUNT : %d\" % total_count)
        print(\"TOTAL IP UNIQUE COUNT : %d\" % len(data))

        return data

    def import_file(self):
        print(\"IMPORT FILE\")
        data = {}
        with open(self.maltrail_path_file, \"r\") as f:
            for line in f:
                line_split = line.split(\",\")
                data[line_split[0]] = [tag.replace(\"\n\", \"\") for tag in line_split[1:]]

        return data

    def export_file(self, data):
        print(\"EXPORT FILE\")
        with open(self.maltrail_path_file, \"wb\") as f:
            for ip in data:
                f.write(\"%s,%s\n\" % (ip, \",\".join(data[ip])))

    def export_redis(self, data):
        print(\"EXPORT REDIS\")
        pipe = self.redis_cli.pipeline()
        for ip in data:
            pipe.hset(str(self) + \"_TMP\", ip, \",\".join(data[ip]))

        pipe.rename(str(self) + \"_TMP\", self.__str__())
        pipe.execute()

    def maj_required_file(self):
        if not os.path.isfile(self.maltrail_path_file) or abs(os.path.getmtime(self.maltrail_path_file) - time.time()) > 24 * 3600:
            return True

        return False

    def maj_required_redis(self):
        return not self.redis_cli.exists(str(self))

    def update(self, force=False):
        if not self.maj_required_file() and not self.maj_required_redis() and not force:
            print(\"No need to update\")
            return

        if self.maj_required_file() or force:
            data = self.fetch()
            if len(data):
                self.export_file(data)
                self.export_redis(data)

        elif self.maj_required_redis():
            self.export_redis(self.import_file())

    def __get_proxy_conf(self):
        proxy = None

        if os.path.exists(\"/etc/rc.conf\"):
            http_proxy  = None
            https_proxy = None
            ftp_proxy   = None

            try:
                tmp = open(\"/etc/rc.conf\").read()
                lst = re.findall(\"http_proxy='(.*)'\", tmp)
                if len(lst):
                    http_proxy = lst[0]
                    if http_proxy == \"\":
                        http_proxy = lst[1]

                lst = re.findall(\"https_proxy='(.*)'\", tmp)
                if len(lst):
                    https_proxy = lst[0]
                
                lst = re.findall(\"ftp_proxy='(.*)'\", tmp)
                if len(lst):
                    ftp_proxy = lst[0]

                proxy = {
                    \"http\" : http_proxy,
                    \"https\": https_proxy,
                    \"ftp\"  : ftp_proxy
                }

            except:
                pass

        return proxy


if __name__ == \"__main__\":
    m = Maltrail()

    if len(sys.argv) > 1 and sys.argv[1] == \"--force\":
        m.update(force=True)
    elif len(sys.argv) == 1:
        m.update()
    else:
        print(\"--force to force update\")

" > /home/vlt-gui/vulture/crontab/vlt-gui/mailtrail.minute

/bin/chmod 750 /home/vlt-gui/vulture/crontab/vlt-gui/mailtrail.minute
/usr/sbin/chown vlt-gui:vlt-gui /home/vlt-gui/vulture/crontab/vlt-gui/mailtrail.minute