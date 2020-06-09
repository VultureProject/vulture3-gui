#!/usr/bin/python
#-*- coding: utf-8 -*-
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
__author__ = "Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Class used to perform SSO forward requests'


# Django system imports
from django.conf                           import settings

# Django project imports
from vulture_toolkit.system.http_utils     import dict_to_multipart, get_uri_fqdn

# Extern modules imports
from json                                  import dumps as json_dumps
from re                                    import compile, IGNORECASE
from requests                              import Session
from requests.adapters                     import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from ssl                                   import CERT_REQUIRED, CERT_NONE

# Logger configuration imports
import logging
logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('portal_authentication')


# Global variables
vulture_custom_agent = 'Vulture/3 (FreeBSD; Vulture OS)'


header_regex = compile("%\{(\w+)\}\w") # example %{REMOTE_ADDR}s


class SSLAdapter(HTTPAdapter):
    """ "Transport adapter" that allows us to use TLSv1 """
    def __init__(self, ssl_version=None, **kwargs):
        self.ssl_version = ssl_version
        super(SSLAdapter, self).__init__(**kwargs)


    def init_poolmanager(self, connections, maxsize, block=False):
         self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_version=self.ssl_version)



class SSOClient(object):
    def __init__(self, vulture_user_agent, request, headers_in, client_certificate, ssl_context):
        """
		:param logger: logger instance
		:param uri: The 'action' uri where to post the form
		:param req: The request from the user browser, used to get referer, user-agent...
		:param data: A dict containing data to be posted
		:param cookie_data: A dict containing data to be sent as Cookies
		:param app: The app object to get its configuration
		:param cookie_from_fetch: the cookie returned by the app when fetching the login page for the first time
		:return a tuple (response: an urllib2 response, response_body: the SSO response body)
		"""
        self.session = Session()
        self.ssl_context = ssl_context
        self.verify_certificate = False
        self.client_side_cert = None
        if ssl_context:
            # Only compatible with request-2.18.1 !!!
            self.session.mount("https://", SSLAdapter(ssl_context.protocol))
            self.verify_certificate = "/home/vlt-sys/Engine/conf/certs/" if ssl_context.verify_mode == CERT_REQUIRED else CERT_NONE
            self.client_side_cert = client_certificate
            logger.debug("SSOClient::_init_: SSL/TLS context successfully created")

        user_agent = request.META.get("HTTP_USER_AGENT", None)
        if vulture_user_agent:
            self.session.headers.update({'User-Agent': vulture_custom_agent})
        else:
            self.session.headers.update({'User-Agent': user_agent or vulture_custom_agent})
        logger.debug("SSOClient::_init_: SSOClient user-agent used is '{}'".format(self.session.headers.get("User-Agent")))

        referer = request.META.get("HTTP_REFERER", None)
        if referer:
            self.session.headers.update({'Referer': referer})
            logger.debug("SSOClient::_init_: SSOClient referer used is '{}'".format(self.session.headers.get("Referer")))

        for header in headers_in:
            # If the header name matches "%{.+}s"
            header_val = header.value
            header_match = header_regex.search(header.value)
            if header_match:
                # Get the value in request META
                header_val = request.META.get(header_match.group(1), None)
                if not header_val:
                    logger.error("SSOClient::_init_: Variable '{}' not found in request infos, it will be sent empty.")
            if header.name.lower() == "cookie":
                self.add_cookies(header_val)
            else:
                self.session.headers.update({header.name: header_val})
        # List of cookies that must not be sent to the client
        self.banned_cookies = list()


    def add_cookies(self, cookies):
        if isinstance(cookies, dict):
            for key,item in cookies.items():
                self.session.cookies.set(key, item)
        if isinstance(cookies, str):
            for key,item in self.get_cookie_values(cookies).items():
                self.session.cookies.set(key, item)


    def get_url_metaredirect(self, http_body):
        try:
            redirect_re = compile('<meta[^>]*?url=\s*(.*?)["\']', IGNORECASE)
            match       = redirect_re.search(http_body)
            if match:
                return match.groups()[0].strip()
        except:
            pass
        return None


    def encode_body(self, response):
        if response.encoding and response.encoding.lower() != "utf-8":
            try:
                return response.content.encode('utf-8')
            except:
                return response.content
        else:
            return response.content


    def add_cookie_W_path(self, response, cookie_name, cookie_value, portal_url, is_http_only, expire):
        # Path of cookie
        path = '/'+'/'.join(portal_url.split('/')[3:])
        # Domain of cookie
        domain = portal_url.split('/')[2].split(':')[0]
        response.set_cookie(cookie_name, cookie_value, domain=domain, path=path, httponly=is_http_only, expires=expire,
                            secure=portal_url.startswith('https'))
        return response


    def fill_response(self, response, final_response, app_uri):
        for key,item in response.headers.items():
            if key.lower() == 'location' and not item.startswith('http'):
                if not item.startswith('/'):
                    final_response['Location'] = get_uri_fqdn(app_uri) + '/' + item
                else:
                    final_response['Location'] = get_uri_fqdn(app_uri) + item
            elif key.lower() != 'set-cookie' and key.lower() != 'www-authenticate':
                final_response[key] = item
        for cookie in self.session.cookies:
            if cookie.name not in self.banned_cookies and not cookie.is_expired():
                final_response = self.add_cookie_W_path(final_response, cookie.name, cookie.value, app_uri,
                                                        "HttpOnly" in cookie._rest.keys(), cookie.expires)

        return final_response


    def get(self, urls, follow_redirect, timeout=5, get_params=None):
        """
        Get the page requested with requests.Session
        Encode in utf-8 if necessary 
        Follow meta-redirect
        Doesn't handle exception
        Return: the url requested, the response
        """
        if not isinstance(urls, list):
            urls = [urls]
        response = None
        error = None
        for url in urls:
            try:
                response = self.session.get(url, params=get_params, verify=self.verify_certificate, cert=self.client_side_cert,
                                            allow_redirects=follow_redirect, timeout=(timeout, timeout))
                response_url = response.url
                break
            except Exception as e:
                error = e
                logger.error("SSO_CLIENT::get:: Failed to fetch url '{}' : {}".format(url, e))
                continue

        if response is None:
            raise error or Exception("No response retrieved")

        # Check if we have to follow a meta-redirect
        redirect_url = self.get_url_metaredirect(self.encode_body(response))
        if redirect_url and follow_redirect:
            response_url, response = self.get(redirect_url, follow_redirect)

        return response_url, response


    def post(self, urls, content_type, post_data, follow_redirect, timeout=5):
        if content_type == 'json':
            post_data = json_dumps(post_data)
            self.session.headers.update({'Content-Type': "application/json"})
        elif content_type == 'default':
            # No need because requests do it by default
            # post_datas = urlencode(post_data)
            self.session.headers.update({'Content-Type': "application/x-www-form-urlencoded"})
        elif content_type == 'multipart':
            content_type_hdr, post_data = dict_to_multipart(post_data)
            self.session.headers.update({'Content-Type': content_type_hdr})

        if not isinstance(urls, list):
            urls = [urls]
        response = None
        error = None
        for url in urls:
            try:
                response = self.session.post(url, data=post_data, verify=self.verify_certificate,
                                             cert=self.client_side_cert, allow_redirects=follow_redirect,
                                             timeout=(timeout, timeout))
                url = response.url
                break
            except Exception as e:
                error = e
                logger.error("Failed to fetch URL '{}' : {}".format(url, e))

        if response is None:
            raise error or Exception("No response retrieved")

        redirect_url = self.get_url_metaredirect(self.encode_body(response))
        if redirect_url and follow_redirect:
            url, response_body = self.get(redirect_url, follow_redirect)

        return url, response


    def advanced_sso_perform(self, matched, application, response):
        # First make the additionnal get request
        # Because if we do, no need to replace content
        """ Check if we want to perform an additional GET request after SSO Request
        """
        if application.sso_after_post_request_enabled and application.sso_after_post_request:
            after_sso_url = application.sso_after_post_request
            if matched:
                i = 1
                for pattern in matched.groups():
                    after_sso_url = after_sso_url.replace('$'+str(i), pattern)
                    i += 1
            try:
                sso_response = self.get(after_sso_url, True)[1]  # self.get() returns a tuple (url, response)
                return sso_response

            except Exception as  e:
                logger.error("SSOClient::advanced_sso_perform: Unable to GET url '{}' : ".format(after_sso_url))
                logger.exception(e)

        elif application.sso_replace_content_enabled and application.sso_replace_pattern and application.sso_replace_content:
            try:
                sso_replace_pattern = application.sso_replace_pattern
                sso_replace_content = application.sso_replace_content
                if matched:
                    i = 1
                    for pattern in matched.groups():
                        sso_replace_pattern = sso_replace_pattern.replace('$'+str(i), pattern.decode('utf8'))
                        sso_replace_content = sso_replace_content.replace('$'+str(i), pattern.decode('utf8'))
                        i += 1
                regex = compile(sso_replace_pattern.encode('utf8'))
                sso_response_body = regex.sub(sso_replace_content.encode('utf8'), response.content)

                return sso_response_body

            except Exception as  e:
                logger.error("SSOClient::advanced_sso_perform: Error while replacing patterns : {}".format(e))

        return response.content

