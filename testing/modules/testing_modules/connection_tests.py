import os
import re

import requests
from testing.core.testing_module import TestingModule


class Module(TestingModule):
    """
    Testing if the Vulture is connected to the download.vultureproject.org update API
    """

    def __str__(self):
        return "Connection to VultureProject Website"

    @staticmethod
    def connect_dl_vultureproject_org():
        """
        """
        url = "https://download.vultureproject.org"
        proxy = None
        if os.path.exists("/etc/rc.conf"):
            http_proxy  = None
            https_proxy = None
            ftp_proxy   = None
            try:
                with open("/etc/rc.conf") as tmp:
                    buf=tmp.read()
                    lst = re.findall('http_proxy="(.*)"', buf)
                    if len(lst):
                        http_proxy = lst[0]
                        if http_proxy == "":
                            http_proxy = lst[1]

                    lst = re.findall('https_proxy="(.*)"', buf)
                    if len(lst):
                        https_proxy = lst[0]
                    elif http_proxy:
                        https_proxy = http_proxy

                    lst = re.findall('ftp_proxy="(.*)"', buf)
                    if len(lst):
                        ftp_proxy = lst[0]
                    elif http_proxy:
                        ftp_proxy = http_proxy

                    if http_proxy and http_proxy[:7] != "http://":
                        http_proxy = "http://"+http_proxy
                    if https_proxy and https_proxy[:7] != "http://":
                        https_proxy = "http://"+https_proxy
                    if ftp_proxy and ftp_proxy[:7] != "http://":
                        ftp_proxy = "http://"+ftp_proxy

                    proxy = {
                        "http" : http_proxy,
                        "https": https_proxy,
                        "ftp"  : ftp_proxy
                    }

            except:
                pass

        f = None
        try:
            f = requests.get(url, verify=True, proxies=proxy)
        except:
            pass
        assert f, "Unable to contact download.vultureproject.org"
