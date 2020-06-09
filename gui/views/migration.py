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
__author__ = "Hubert Loiseau"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to import vulture2 database into vulture3'


# Django system imports
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from mongoengine.django.auth import MongoEngineBackend

# Django project imports
from gui.forms.system_settings import MigrationForm
from gui.models.application_settings import Application, ContentRule, HeaderIn, HeaderOut, ListenAddress, ProxyBalancer, ProxyBalancerMember
from gui.models.modlog_settings import ModLog
from gui.models.modssl_settings import ModSSL
from gui.models.network_settings import Interface, Listener
from gui.models.rewrite_settings import RewriteRule, Rewrite
from gui.models.ssl_certificate import SSLCertificate
from gui.models.system_settings import BaseAbstractRepository, Cluster
from gui.models.worker_settings import Worker

# Required exceptions imports

# Extern modules imports
from bson.objectid import ObjectId
from multiprocessing import Process
from OpenSSL import crypto
from sqlite3 import connect as sqlite3_connect

# Logger configuration imports
import logging
logger = logging.getLogger('listeners')


def migration(request):
    """
    REMINDER : pkg install databases/py-sqlite3 && pkg install sqlite3
    get the file uploaded to generate a slite3 connector
    calls main method processing to spawn each field of vulture database with the connector
    """
    form = MigrationForm(request.POST or None)
    if request.method == 'POST':
        try:
            # store the sqlite3 db file to a temp path
            default_storage.DEFAULT_FILE_STORAGE = '/tmp/'
            logger.info("Starting import process")
            f = request.FILES['file']
            f.content_type = "application/x-sqlite3"
            path = default_storage.save('tmp/migration-temp.db', ContentFile(f.read()))
            conn = sqlite3_connect('/home/vlt-gui/vulture/static/'+path)
            # start a subprocess for processing datas
            m = Process(name='script', target=processing, args=[conn, ])
            m.start()
            return HttpResponseRedirect('/migration/')
        except:
            raise



    else:
        return render_to_response('migration_vulture.html', {'form': form}, context_instance=RequestContext(request))


def processing(conn):
            """
            take the sqlite connector to call every method
            each method pass a dictionary to another to retrieve objects generated with their id
            """
            import_loadbalancer(conn)
            modssl_dict = import_certificate(conn)
            headerid_dict = import_headerin(conn)
            modlog_dict = import_logprofil(conn)
            appid_application = import_application(conn, headerid_dict, modlog_dict, modssl_dict)
            import_rewrite_rules(conn, appid_application)
            logger.info("End of import process")


def import_application(conn, headerid, modlog_dict, modssl_dict):
    """
    import all applications from sqlite3
    :param conn: sqlite3 connector
    :param headerid: dict to retrieve sqlite3 id of header generated in previous method
    :param modlog_dict: dict to retrieve sqlite3 id of modlog generated in previous method
    :param modssl_dict: dict to retrieve sqlite3 id of ssl profile generated in previous method
    """
    appid_application = dict()
    app_log = dict()
    appid_logid = dict()
    appid_headerid = dict()
    appid_intfid = dict()
    listenertolistenaddress = dict()
    appid_interfaceid = dict()

    cluster = Cluster.objects.get()
    node = cluster.get_current_node()
    # select the first interface which is em0
    # FIXME: ask user on which interface to bind all the listeners
    # FIXME : Obsolet method
    em = node.get_interfaces()[0].id
    
    # generate list for every table in sqlite database
    
    intf = conn.cursor()
    intf.execute("SELECT * FROM intf")
    intf_sql = intf.fetchall()

    app = conn.cursor()
    app.execute("SELECT * FROM app")
    application_sql = app.fetchall()

    app_intf = conn.cursor()
    app_intf.execute("SELECT * FROM app_intf")
    app_intf_sql = app_intf.fetchall()

    log = conn.cursor()
    log.execute("SELECT * FROM log")
    log_sql = log.fetchall()
    
    header = conn.cursor()
    header.execute("SELECT * FROM header")
    header_sql = header.fetchall()

    plugincontent = conn.cursor()
    plugincontent.execute("SELECT * FROM plugincontent")
    plugincontent_sql = plugincontent.fetchall()

    pluginheader = conn.cursor()
    pluginheader.execute("SELECT * FROM pluginheader")
    pluginheader_sql = pluginheader.fetchall()

    logger.info("Importing network interfaces")

    # Retrieve index in database of each name fields of "app_intf" table
    col_name_list_app_intf = [tuple[0] for tuple in app_intf.description]
    app_intf_id = col_name_list_app_intf.index("id")
    app_intf_app_id = col_name_list_app_intf.index("app_id")
    app_intf_intf_id = col_name_list_app_intf.index("intf_id")

    # Retrieve index in database of each name fields of "intf" table
    col_name_list_intf = [tuple[0] for tuple in intf.description]
    intf_id = col_name_list_intf.index("id")
    intf_name = col_name_list_intf.index("name")
    intf_ip = col_name_list_intf.index("ip")
    intf_port = col_name_list_intf.index("port")
    intf_log_id = col_name_list_intf.index("log_id")

    # Retrieve index in database of each name fields of "app" table
    col_name_list_app = [tuple[0] for tuple in app.description]
    app_id = col_name_list_app.index("id")
    app_friendly_name = col_name_list_app.index("friendly_name")
    app_name = col_name_list_app.index("name")
    app_url = col_name_list_app.index("url")
    app_log_id = col_name_list_app.index("log_id")
    app_logon_url = col_name_list_app.index("logon_url")
    app_auth_id = col_name_list_app.index("auth_id")
    app_auth_url = col_name_list_app.index("auth_url")
    app_Balancer_Name = col_name_list_app.index("Balancer_Name")
    app_Balancer_Node = col_name_list_app.index("Balancer_Node")
    app_enable_ssl = col_name_list_app.index("enable_ssl")
    app_ssl_configuration_id = col_name_list_app.index("ssl_configuration_id")

    # Retrieve index in database of each name fields of "log" table
    col_name_list_log = [tuple[0] for tuple in log.description]
    logs_id = col_name_list_log.index("id")
    logs_name = col_name_list_log.index("name")
    logs_level = col_name_list_log.index("level")
    logs_format = col_name_list_log.index("format")

    # Retrieve index in database of each name fields of "header" table
    col_name_list_header = [tuple[0] for tuple in header.description]
    header_id = col_name_list_header.index("id")
    header_name = col_name_list_header.index("name")
    header_type = col_name_list_header.index("type")
    header_value = col_name_list_header.index("value")
    header_app_id = col_name_list_header.index("app_id")

    # Retrieve index in database of each name fields of "pluginheader" table
    col_name_list_plugin_header = [tuple[0] for tuple in pluginheader.description]
    pluginheader_id = col_name_list_plugin_header.index("id")
    pluginheader_app_id = col_name_list_plugin_header.index("app_id")
    pluginheader_pattern = col_name_list_plugin_header.index("pattern")
    pluginheader_type = col_name_list_plugin_header.index("type")
    pluginheader_options = col_name_list_plugin_header.index("options")
    pluginheader_options1= col_name_list_plugin_header.index("options1")

    # Retrieve index in database of each name fields of "plugincontent" table
    col_name_list_plugin_content = [tuple[0] for tuple in plugincontent.description]
    plugincontent_id = col_name_list_plugin_content.index("id")
    plugincontent_app_id = col_name_list_plugin_content.index("app_id")
    plugincontent_pattern = col_name_list_plugin_content.index("pattern")
    plugincontent_type = col_name_list_plugin_content.index("type")
    plugincontent_options = col_name_list_plugin_content.index("options")
    plugincontent_options1 = col_name_list_plugin_content.index("options1")

    for i in app_intf_sql:
        appid_interfaceid[i[app_intf_app_id]] = i[app_intf_intf_id]

    # generate every listener on the current node
    for i in intf_sql:
        logger.info("Listener " + str(i[intf_name]))
        node = cluster.get_current_node()
        listener = Listener()
        listener.alias = str(i[intf_name])
        listener.ip = str(i[intf_ip])
        listener.version = "4"
        listener.prefixlen = "255.255.255.0"
        listener.is_carp = False
        listener.is_physical = False
        listener.is_gui = False
        listener.is_ghost = False
        listener.save()

        # dictionary to link listener to listen address
        listenertolistenaddress[i[intf_id]] = listener

        logger.info("Creating listener " + str(listener.alias))

        selected_intf = Interface.objects.with_id(em)
        selected_intf.inet_addresses.append(listener)  # append the listen address in the interface
        selected_intf.save()
        listener.deploy_inet()
        node.interfaces[intf_id] = selected_intf  # add the interface modified into the node
        node.save()

    appid_listenaddress = dict()
    logger.info("End of network interfaces import process")
    logger.info("Importing applications")
    for app in application_sql:

        application = Application()
        outgoing_headers = []
        content_rules = []
        headers_in = []
        public_dir = ""

        # Retrieve fqdn and public_dir from app[app_friendly_name]
        tmp = app[app_friendly_name].split("/")
        fqdn = tmp[0]
        public_dir = app[app_friendly_name].replace(fqdn, "")
        if not public_dir.endswith('/'):
            public_dir = public_dir + '/'

        # if there's an authentication portal (app[app_logon_url]) then auth = True
        if app[app_logon_url] is None:
            need_auth = False
        else:
            need_auth = True

        # retrieve type of application
        if app[app_url].split(":")[0] == "balancer":  # if the url start with "balancer://" , app_type=balanced
            app_type = "balanced"
            # [app_Balancer_Name] = balancer uri
            application.proxy_balancer = ProxyBalancer.objects.get(name=app[app_Balancer_Name])
        else:
            app_type = app[app_url].split(":")[0]  # otherwise; filetype is before ":" (http,https,ftp...)

        # retrieve log profile linked to this app (we generated the profile earlier, now we find it back)
        for j in log_sql:
            if app[app_log_id] == j[logs_id]:  # if app[app_log_id] =logs_id of the application match => link
                app_log[app[app_friendly_name]] = j[logs_level]  # link appname -> log_level found
                appid_logid[app[app_id]] = j[logs_id]

        # generate a listen_address for this app based on the interface generated earlier
        for j in intf_sql:
            if appid_interfaceid[app[app_id]] == j[intf_id]:  # find link  between interface and app_id
                interface_id = j[intf_id]
                intf.execute("SELECT * FROM intf WHERE id =?", (interface_id,))  # select interface in db with link
                interface = intf.fetchone()
                appid_intfid[app[app_id]] = interface[0]  # appid_interfaceid appid:interfaceid
                listen_address = ListenAddress()
                # apprend address of listener to current listen address
                listen_address.address = listenertolistenaddress[j[intf_id]]
                listen_address.port = str(j[intf_port])
                listen_address.redirect = False
                listen_address.redirect_port = ""
                # if this app uses a specific SSL profile, then load it
                if app[app_enable_ssl] == 1:
                    listen_address.ssl_profile = modssl_dict[app[app_ssl_configuration_id]]
                listen_address.save()
                appid_listenaddress[app[app_id]] = listen_address

        # Retrieve all request headers except SSL headers (not managed in vulture3)
        for j in header_sql:
            if app[app_id] == j[header_app_id]:
                if j[header_name] != "SSL_CLIENT_S_DN_CN" and \
                                j[header_name] != "SSL_CLIENT_S_DN_O" and j[header_name] != "SSL_CLIENT_S_DN_OU":
                    appid_headerid[str(app[app_id])] = j[header_id]
                    headers_in.append(headerid[j[header_id]])

        # Retrieve headers in "pluginheader" table
        for j in pluginheader_sql:
            if j[pluginheader_app_id] == app[app_id]:
                headerin = HeaderIn()
                headerin.name = j[pluginheader_pattern]
                headerin.action = "edit"
                headerin.value = j[pluginheader_options]
                headerin.replacement = j[pluginheader_options1]
                headerin.condition = "always"
                headerin.save()
                headers_in.append(headerin)

        """ generate each type of header out and contentrule. Stored in the same table "plugincontent"
         with non consistent fields."""
        for i in plugincontent_sql:
            if i[plugincontent_type] == "Rewrite Content" and i[plugincontent_app_id] == app[app_id]:
                content_rule = ContentRule()
                content_rule.path_type = "files"
                content_rule.path = ""
                content_rule.types = ""
                content_rule.flags = ""
                content_rule.deflate = True
                content_rule.inflate = False
                content_rule.pattern = i[plugincontent_pattern]
                content_rule.replacement = i[plugincontent_options]
                content_rule.save()
                content_rules.append(content_rule)
            if i[plugincontent_type] == "Rewrite Link" and i[plugincontent_app_id] == app[app_id]:
                headerout = HeaderOut()
                headerout.name = "Link"
                headerout.value = i[plugincontent_options]
                headerout.replacement = i[plugincontent_pattern]
                headerout.action = "edit"
                headerout.condition = "always"
                headerout.save()
                outgoing_headers.append(headerout)
            if i[plugincontent_type] == "Location" and i[plugincontent_app_id] == app[app_id]:
                headerout = HeaderOut()
                headerout.name = i[plugincontent_pattern]
                headerout.value = i[plugincontent_options1]
                headerout.replacement = i[plugincontent_options]
                headerout.action = "edit"
                headerout.condition = "always"
                headerout.save()
                outgoing_headers.append(headerout)

        # retrieve the Vulture Internal Database repository for authentication.
        repo_list = BaseAbstractRepository.get_auth_repositories()
        for repo in repo_list:
            if repo.is_internal and isinstance(repo.get_backend(), MongoEngineBackend):
                auth_backend = repo

        # select the default worker
        worker = Worker.objects.first()
        # auth_backend = ""
        # populate each field of app generated before
        application.name = app[app_friendly_name]
        application.type = app_type
        application.public_name = fqdn
        application.private_uri = app[app_url]
        application.public_dir = public_dir
        application.proxy_add_header = False
        application.access_mode = []
        # retrieve log profile generated that have a link with this app
        for j in log_sql:
            application.log_custom = modlog_dict[appid_logid[app[app_id]]]
            tmp = application.log_custom.format
            tmp = tmp.replace("\\", "")  # remove escaping chars from mongo
            application.log_custom.format = tmp
        application.log_level = app_log[app[app_friendly_name]]
        application.headers_in = headers_in
        application.headers_out = outgoing_headers
        application.content_rules = content_rules
        application.listeners.append(appid_listenaddress[app[app_id]])
        application.force_tls = False
        application.worker = worker
        application.methods = "HEAD,GET,POST"
        application.enable_h2 = False
        application.enable_rpc = False
        application.need_auth = need_auth
        if need_auth:
            application.auth_type = "basic"
            application.auth_backend = str(auth_backend)
            application.auth_backend_fallback = str(auth_backend)
            application.auth_portal = str(application.private_uri + app[app_logon_url])
            application.auth_timeout = "900"
            application.auth_timeout_restart = True
        application.sso_enabled = False
        if application.sso_enabled:
            application.sso_forward = "form"
            application.sso_forward_basic_mode = "autologon"
            application.sso_forward_only_login = False
            application.sso_forward_basic_url = "http=//your_internal_app/action.do?what=login"
            application.sso_forward_follow_redirect = False
            application.sso_forward_return_post = False
            application.sso_forward_content_type = "default"
            application.sso_url = "http://your_internal_app/action.do?what=login"
            application.sso_vulture_agent = False
            application.sso_capture_content_enabled = False
            application.sso_capture_content = ""
            application.sso_replace_content_enabled = False
            application.sso_replace_content = "By previously captured '$1'/"
            application.sso_after_post_request_enabled = False
            application.sso_after_post_request = "http://My_Responsive_App.com/Default.aspx"
            application.sso_after_post_replace_content_enabled = False
            application.sso_after_post_replace_content = ""
        logger.info("Saving application: " + str(application))
        application.save()
        appid_application[app[app_id]] = application.id
    logger.info("End of applications import process")
    return appid_application


def import_logprofil(conn):
    """
    import all logprofil
    :param: logs_name: log profil name
    :param: logs_format: log profil format
    :return: modlog_dict: dict to link log profile in sqlite to log_profile object in mongodb created
    """
    logger.info("Importing log profiles")

    log = conn.cursor()
    log.execute("SELECT * FROM log")
    log_sql = log.fetchall()

    # Retrieve index in database of each name fields of "log" table
    col_name_list_log = [tuple[0] for tuple in log.description]
    logs_id = col_name_list_log.index("id")
    logs_name = col_name_list_log.index("name")
    logs_format = col_name_list_log.index("format")

    app = conn.cursor()
    app.execute("SELECT * FROM app")
    application_sql = app.fetchall()

    # Retrieve index in database of each name fields of "app" table
    col_name_list_app = [tuple[0] for tuple in app.description]
    app_log_id = col_name_list_app.index("log_id")

    modlog_dict = dict()
    used_log_list = list()

    # Avoid duplicates values
    for appli in application_sql:
        if appli[app_log_id] not in used_log_list:
            used_log_list.append(appli[app_log_id])

    for i in log_sql:
        if i[logs_id] in used_log_list:
            modlog = ModLog()
            modlog.name = str(i[logs_name])
            modlog.format = i[logs_format]
            # remove escaping characters \\ and ' generated in mongodb
            tmp = modlog.format
            tmp = tmp.replace('\\', '')
            tmp = tmp.replace('"', '')
            modlog.format = tmp
            modlog.separator = "space"
            modlog.repository_type = "file"
            # dictionary id_logprofil -> object_modlog
            modlog_dict[i[logs_id]] = modlog  # dictionary id_logprofil -> object_modlog
            modlog.save()
    logger.info("End of log profiles importing process")
    return modlog_dict


def import_certificate(conn):
    """
    Import all SSL certificates
    :param: ssl_conf_id: ssl certificate id
    :param: ssl_conf_cert: ssl cert chain
    :param: ssl_conf_key: ssl key chain
    :param: ssl_conf_ca: ssl ca chain
    :param: ssl_conf_ssl_protocol: ssl protocols supported
    :param: ssl_conf_ssl_cipher_suite: ssl ciphers suite
    :return modssl_dict: dict to link sslprofile id in sqlite to object created in mongodb
    """
    logger.info("Importing SSL profiles and certificates")
    ssl_conf = conn.cursor()
    ssl_conf.execute("SELECT * FROM ssl_conf")
    ssl_conf_sql = ssl_conf.fetchall()

    app = conn.cursor()
    app.execute("SELECT * FROM app")
    application_sql = app.fetchall()

    # Retrieve index in database of each name fields of "app" table
    col_name_list_app = [tuple[0] for tuple in app.description]
    ssl_configuration_id = col_name_list_app.index("ssl_configuration_id")
    auth_id = col_name_list_app.index("auth_id")

    # Retrieve index in database of each name fields of ""ssl_conf" table
    col_name_list_ssl_conf = [tuple[0] for tuple in ssl_conf.description]
    ssl_conf_id = col_name_list_ssl_conf.index("id")
    ssl_conf_cert = col_name_list_ssl_conf.index("cert")
    ssl_conf_key = col_name_list_ssl_conf.index("key")
    ssl_conf_ca = col_name_list_ssl_conf.index("ca")
    ssl_conf_ssl_protocol = col_name_list_ssl_conf.index("ssl_protocol")
    ssl_conf_ssl_cipher_suite = col_name_list_ssl_conf.index("ssl_cipher_suite")

    modssl_dict = dict()
    used_ssl_list = list()

    # Avoid unused ssl_profile
    for app in application_sql:
        used_ssl_list.append(app[ssl_configuration_id])

    for i in ssl_conf_sql:
        # if ssl_profile id is in list of used ssl profile by application, we import it
        if i[ssl_conf_id] in used_ssl_list and i[ssl_conf_cert]:
            # then we create and populate the ssl profile
            verify_client = "none"
            modssl = ModSSL()
            modssl.name = "SSL_profile_" + str(i[ssl_conf_id])
            if "+SSLv3" in i[ssl_conf_ssl_protocol]:
                modssl.protocols = "+SSLv3"
            if "+TLSv1" in i[ssl_conf_ssl_protocol]:
                modssl.protocols = "+TLSv1"
            if "+TLSv1.1" in i[ssl_conf_ssl_protocol]:
                modssl.protocols = "+TLSv1.1"
            if "+TLSv1.2" in i[ssl_conf_ssl_protocol]:
                modssl.protocols = "+TLSv1.2"
            modssl.ciphers = i[ssl_conf_ssl_cipher_suite]
            modssl.engine = "builtin"
            # if auth method is SSL or SSL|Kerberos, verify client certificate
            for app in application_sql:
                if app[auth_id] == "6" or app[auth_id] == "5":
                    verify_client = "require"

            modssl.verifyclient = verify_client
            modssl.engine = "builtin"

            # then we create the linked certificate of this ssl profile
            cert = SSLCertificate()
            cert.cert = ""
            cert.key = ""
            cert.chain = ""
            certificate = ""

            # remove \r in string cert, key, ca
            for j in i[ssl_conf_cert].split("\r"):
                certificate = certificate + j

            cert.cert = str(i[ssl_conf_cert])
            cert.key = str(i[ssl_conf_key])
            cert.chain = str(i[ssl_conf_ca])
            x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert.cert)

            # retrieve each fields of subject if it exists
            for j in x509.get_subject().get_components():
                if j[0] == "CN":
                    cert.cn = j[1]
                elif j[0] == "C":
                    cert.c = j[1]
                elif j[0] == "ST":
                    cert.st = j[1]
                elif j[0] == "L":
                    cert.l = j[1]
                elif j[0] == "O":
                    cert.o = j[1]
                elif j[0] == "OU":
                    cert.ou = j[1]

            # retrieve issuer informations
            cert.issuer = str(x509.get_issuer()).split("<X509Name object '")[1].split("'>")[0]
            # parse date format
            cert.validfrom = str(x509.get_notBefore())[0:4]+"-"+str(x509.get_notBefore())[4:6]\
                             +"-"+str(x509.get_notBefore())[6:8]+" "+str(x509.get_notBefore())[8:10]\
                             +":"+str(x509.get_notBefore())[10:12]+":"+str(x509.get_notBefore())[12:14]
            cert.validtill = str(x509.get_notAfter())[0:4]+"-"+str(x509.get_notAfter())[4:6]\
                             +"-"+str(x509.get_notAfter())[6:8]+" "+str(x509.get_notAfter())[8:10]\
                             +":"+str(x509.get_notAfter())[10:12]+":"+str(x509.get_notAfter())[12:14]

            # name is issuer
            cert.name = str(x509.get_subject()).split("<X509Name object '")[1].split("'>")[0]
            cert.save()
            modssl.certificate = cert
            modssl.save()
            modssl_dict[i[ssl_conf_id]] = modssl
    logger.info("End of SSL profiles and certificates importing process")
    return modssl_dict


def import_headerin(conn):
    """
    Generate headerin objects in mongo and return a dictionnary to link headerid to object created
    :param:  header_id: headerin id
    :param: header_name: type of header
    :param: header_value: header value to set
    :return: headerid_headerin dict to link headerid in sqlite to header_in object in mongodb created
    """
    logger.info("Importing headers_in")

    header = conn.cursor()
    header.execute("SELECT * FROM header")
    header_sql = header.fetchall()

    # Retrieve index in database of each name fields
    col_name_list_header = [tuple[0] for tuple in header.description]
    header_id = col_name_list_header.index("id")
    header_name = col_name_list_header.index("name")
    header_type = col_name_list_header.index("type")
    header_value = col_name_list_header.index("value")
    header_app_id = col_name_list_header.index("app_id")
    headerid_headerin = dict()

    # retrieve fields of header except ssl headers
    for i in header_sql:
        if i[header_name] != "SSL_CLIENT_S_DN_CN" and i[header_name] != "SSL_CLIENT_S_DN_O" \
                and i[header_name] != "SSL_CLIENT_S_DN_OU":
            headerin = HeaderIn()
            headerin.name = i[header_name]
            headerin.action = 'set'
            headerin.condition = 'always'
            headerin.value = i[header_value]
            headerin.save()
            headerid_headerin[i[header_id]] = headerin
    logger.info("End of header_in importing process")
    return headerid_headerin  # return dict headerid->headerin object


def import_loadbalancer(conn):
    """
    Import loadbalancer from app table
    :param: Balancer_Activated
    :param: Balancer_Name: load_balancer uri
    :param: Balancer_Node: balancer node route string (http://10.0.0.1 route=node_0_1;http://10.0.0.2 route=node_0_2)
    :param: Balancer_Algo: method to loadbalance (byrequest)
    """
    logger.info("Importing proxy balancer")
    app = conn.cursor()
    app.execute("SELECT * FROM app")
    app_sql = app.fetchall()

    # Retrieve index in database of each name fields
    col_name_list_app = [tuple[0] for tuple in app.description]
    id = col_name_list_app.index("id")
    Balancer_Activated = col_name_list_app.index("Balancer_Activated")
    Balancer_Name = col_name_list_app.index("Balancer_Name")
    Balancer_Node = col_name_list_app.index("Balancer_Node")
    Balancer_Algo = col_name_list_app.index("Balancer_Algo")

    for app in app_sql:
        if app[Balancer_Activated]:
            try:
                # check if a loadbalancer already exists with the same name
                ProxyBalancer.objects.get(name=app[Balancer_Name])
            except:  # otherwise, create it
                balancer = ProxyBalancer()
                balancer.name = app[Balancer_Name]
                balancer.lbmethod = app[Balancer_Algo]
                balancer.stickysession = "route"
                balancer.stickysessionsep = "."
                # iterate as many time as there's ; (one ; == 1LB)+1
                for j in range(len(app[Balancer_Node].split(";"))):
                    balancer_member = ProxyBalancerMember()
                    balancer_member.uri = app[Balancer_Node].split(";")[j].split()[0].split("//")[1]
                    balancer_member.uri_type = app[Balancer_Node].split(";")[j].split()[0].split(":")[0]
                    balancer_member.route = app[Balancer_Node].split(";")[j].split()[1].split("=")[1]
                    balancer_member.timeout = "60"
                    balancer_member.retry = "60"
                    balancer_member.config = " "
                    balancer_member.lbset = balancer.name
                    balancer_member.save()
                    balancer.members.append(balancer_member)
                balancer.save()
    logger.info("fEnd of proxy balancer importing process")


def import_rewrite_rules(conn, appid_application):
    """
     Import URL rewriting rules located in plugin table
     appid_application dictionary to retrieve which app correspond the rule
     :param: plugin_id: id of URL rewrite rule
     :param: plugin_app_id: application id that uses this rule
     :param: plugin_uri_pattern: regex pattern to match
     :param: plugin_type: type of rule (Rewrite)
     :param: plugin_options: pattern to replace (with flag like : "/pattern/ [R=>301]") (used as name of url rewrite rule)
    """
    plugin = conn.cursor()
    plugin.execute("SELECT * FROM plugin")
    plugin_sql = plugin.fetchall()

    col_name_list_plugin = [tuple[0] for tuple in plugin.description]
    plugin_id = col_name_list_plugin.index("id")
    plugin_app_id = col_name_list_plugin.index("app_id")
    plugin_uri_pattern = col_name_list_plugin.index("uri_pattern")
    plugin_type = col_name_list_plugin.index("type")
    plugin_options = col_name_list_plugin.index("options")

    app = conn.cursor()
    app.execute("SELECT * FROM app")
    app_sql = app.fetchall()

    col_name_list_app = [tuple[0] for tuple in app.description]
    id = col_name_list_app.index("id")
    friendly_name = col_name_list_app.index("friendly_name")

    logger.info("Importing URL Rewrite rules")

    for app in app_sql:
        # list used to store multiple rewrite rules for an unique application rule
        temp = list()
        for i in plugin_sql:
            # only selecte Rewrite entries (avoid logout and favicon)
            if i[plugin_type] == "Rewrite" and i[plugin_app_id] == app[id]:
                try:
                    rewrite = Rewrite()
                    rewrite.name = app[friendly_name]
                    rewriterule = RewriteRule()
                    rewriterule.pattern = i[plugin_uri_pattern]
                    rewriterule.replacement = i[plugin_options].split()[0]
                    rewriterule.flags = i[plugin_options].split()[1].split("[")[1].split("]")[0]
                    rewriterule.save()
                    temp.append(rewriterule)
                except Exception as e:
                    logger.info("exception ", e)
        try:
            for j in temp:
                # append all the rewriterule generated in the rewrite object
                rewrite.rules.append(RewriteRule.objects.with_id(ObjectId(j.id)))
            for i in plugin_sql:
                if i[plugin_app_id] == app[id] and i[plugin_type] == "Rewrite":
                    # check every rule corresponding to the id app[0]
                    rewrite.application.append(Application.objects.with_id(appid_application[app[id]]))
            rewrite.save()
        except:
            pass
    logger.info("End of URL rewrite rules importing process")
