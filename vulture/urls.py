# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from gui.models.repository_settings import ElasticSearchRepository, KerberosRepository, LDAPRepository, MongoDBRepository, OTPRepository, RadiusRepository, \
    SQLRepository, SyslogRepository
from gui.views.generic_delete import DeleteApplication, DeleteAuth, DeleteDataset, DeleteImage, DeleteListener, DeleteLoadBalancer, DeleteModAccess, DeleteModLog, DeleteModSec, DeleteModSecRules, DeleteModSecRulesSet, DeleteModSSL, DeleteNode, DeletePortalTemplate, DeleteProxyBalancer, DeleteRewrite, DeleteSSOProfile, DeleteWorker, RevokeCertificate
from gui.views.generic_list_views import RepositoryListView
from gui.views.generic_repository import ElasticSearchRepositoryEditView, ElasticSearchRepositoryListView, KerberosRepositoryListView, KerberosRepositoryEditView, LDAPRepositoryEditView, \
    LDAPRepositoryListView, MongoDBRepositoryEditView, MongoDBRepositoryListView, OTPRepositoryEditView, OTPRepositoryListView, RadiusRepositoryEditView, RadiusRepositoryListView, SQLRepositoryListView, \
    SQLRepositoryEditView, SyslogRepositoryListView, SyslogRepositoryEditView
from gui.views.generic_views import CloneView

handler403 = 'gui.views.gui_auth.handler403'
handler404 = 'gui.views.gui_auth.handler404'
handler500 = 'gui.views.gui_auth.handler500'

from gui.views.gui_auth import log_in, log_out, unauthorized
from gui.views.agents import agent_zabbix_view
from gui.views.monitor import general, system, network, users, traffic, data, realtime, diagnostic
from gui.views.reporting import map_traffic, report_access, report_security, report_pf, report_data
from gui.views.users import user_list, user_edit
from gui.views.logs import logs, get_logs, export_logs, get_filter, save_filter, del_filter, blacklist_pf
from gui.views.repository_validation_test import sql_connection_test, sql_user_search_test, syslog_connection_test, \
    kerberos_user_search_test, ldap_connection_test, ldap_group_search_test, ldap_user_search_test, \
    radius_user_search_test, mongodb_connection_test, mongodb_user_search_test, elasticsearch_connection_test
from gui.views.migration import migration
from gui.views.sso_profiles import profile_list, profile_edit
from gui.views.cluster import general_settings, edit as cluster_edit, promote, join, remove, redis_promote, update, \
    need_update, launch_update, check_diagnostic, check_vulns, get_vulns
from gui.views.services import ntp_view, restart_ntp, ssh_view, dns_view, pf_view, restart_pf, smtp_view, test_smtp, \
    global_view, loganalyser_view, ipsec_view
from gui.views.cert import cert_list, create, load, load_ca, sign, download as cert_download, edit as cert_edit
from gui.views.network import inet_list, edit_inet
from gui.views.loadbalancer import loadbalancer, edit_loadbalancer
from gui.views.topology import topology
from gui.views.proxybalancer import balancer_list as proxybalancer_list, edit as proxybalancer_edit, \
    clone as proxybalancer_clone
from gui.views.rewrite import rewrite_list, edit as rewrite_edit, clone as rewrite_clone
from gui.views.application import application_list, edit as application_edit, clone as application_clone, ssotest, fetch_ldap_groups
from gui.views.template import template_list, edit as template_edit, clone as template_clone, image_edit
from gui.views.management import reload, reloadall, reloadapp, startall, stopall, start, stop, \
    download as conf_download, status, statusfull
from gui.views.modaccess import access_list, edit as access_edit, clone as access_clone, fetch_ldap_user
from gui.views.modsec import policy_list, edit as modsec_edit, clone as modsec_clone, rulesset_list, clone_rules, \
    edit_rules, edit_file, import_crs, import_scan, add_rules_wl_bl, get_rules_wl_bl
from gui.views.modlog import log_list, edit as log_edit
from gui.views.worker import worker_list, edit as worker_edit, clone as worker_clone
from gui.views.modssl import ssl_list, edit as modssl_edit, clone as modssl_clone
from gui.views.dataset import datasets, dataset_add, dataset_build, dataset_edit, dataset_get, dataset_get_learning, \
    dataset_list, dataset_status, add_wl, learning_edit, generate_wl, remove_logs, remove_logs_learning, print_graph, \
    graph_realtime, svm_view, delete_learning

##############################-GUI ROUTES-##################################
urlpatterns = [
    url(r'^/?$', general, name="monitor_general"),
    url(r'^home/$', general, name="monitor_general"),
    url(r'^accounts/login/', log_in, name="log_in"),
    url(r'^logout/', log_out, name="log_out"),
    url(r'^unauthorized/$', unauthorized, name="unauthorized"),
    url(r'^migration/$', migration, name="migration"),

    # Monitor routes
    url(r'^monitor/general/', general, name="monitor_general"),
    url(r'^monitor/system/', system, name="monitor_system"),
    url(r'^monitor/network/', network, name="monitor_network"),
    url(r'^monitor/users/', users, name="monitor_users"),
    url(r'^monitor/data/', data, name="monitor_data"),
    url(r'^monitor/realtime/', realtime, name="monitor_realtime"),
    url(r'^monitor/diagnostic/', diagnostic, name='monitor_diagnostic'),

    # Reporting routes
    url(r'^reporting/map/', map_traffic, name='reporting_map'),
    url(r'^reporting/access/', report_access, name='reporting_access'),
    url(r'^reporting/security/', report_security, name='reporting_security'),
    url(r'^reporting/pf/', report_pf, name='reporting_pf'),
    url(r'^reporting/data/', report_data, name='reporting_data'),

    # Monitoring-Agents routes
    url(r'^agents/zabbix/(?P<object_id>[A-Fa-f0-9]{24})?$', agent_zabbix_view, name='agents_view'),

    # System routes
    url(r'^system/users/$', user_list, name="user_settings"),
    url(r'^system/users/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', user_edit, name="user_settings"),

    # Status routes
    url(r'^logs/$', logs, name="status_logs"),
    url(r'^logs/get$', get_logs, name="get data logs"),
    url(r'^logs/export/$', export_logs, name="export data logs"),
    url(r'^logs/getfilter/$', get_filter, name="get filter"),
    url(r'^logs/savefilter/$', save_filter, name="save filter"),
    url(r'^logs/delfilter/$', del_filter, name="del filter"),
    url(r'^logs/blacklist_pf/$', blacklist_pf, name="add blacklist to packet filter"),

    # Repository routes
    url(r'^repository/?$', RepositoryListView.as_view(), name="repository_global"),
    url(r'^repository/sql/?$', SQLRepositoryListView.as_view(), name="repository_sql"),
    url(r'^repository/sql/edit/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', SQLRepositoryEditView.as_view(),
        name="repository_sql"),
    url(r'^repository/sql/clone/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', CloneView.as_view(),
        {'obj_type': SQLRepository, 'name_attribute': 'repo_name', 'redirect_url': '/repository/sql/'},
        name="repository_sql"),
    url(r'^repository/sql/delete/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', DeleteAuth.as_view(),
        {'obj_type': SQLRepository, 'redirect_url': '/repository/sql/', 'delete_url': '/repository/sql/delete/'},
        name="repository_sql"),
    url(r'^repository/sql/connection_test/?$', sql_connection_test, name="SQL Connection test"),
    url(r'^repository/sql/user_search_test/?$', sql_user_search_test, name="SQL User Search test"),
    url(r'^repository/syslog/?$', SyslogRepositoryListView.as_view(), name="repository_syslog"),
    url(r'^repository/syslog/edit/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', SyslogRepositoryEditView.as_view(),
        name="repository_syslog"),
    url(r'^repository/syslog/clone/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', CloneView.as_view(),
        {'obj_type': SyslogRepository, 'name_attribute': 'repo_name', 'redirect_url': '/repository/syslog/'},
        name="repository_syslog"),
    url(r'^repository/syslog/delete/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', DeleteAuth.as_view(),
        {'obj_type': SyslogRepository, 'redirect_url': '/repository/syslog/',
         'delete_url': '/repository/syslog/delete/'}, name="repository_syslog"),
    url(r'^repository/syslog/connection_test/?$', syslog_connection_test, name="syslog Connection test"),
    url(r'^repository/kerberos/?$', KerberosRepositoryListView.as_view(), name="repository_kerberos"),
    url(r'^repository/kerberos/edit/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', KerberosRepositoryEditView.as_view(),
        name="repository_kerberos"),
    url(r'^repository/kerberos/clone/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', CloneView.as_view(),
        {'obj_type': KerberosRepository, 'name_attribute': 'repo_name', 'redirect_url': '/repository/kerberos/'},
        name="repository_kerberos"),
    url(r'^repository/kerberos/delete/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', DeleteAuth.as_view(),
        {'obj_type': KerberosRepository, 'redirect_url': '/repository/kerberos/',
         'delete_url': '/repository/kerberos/delete/'}, name="repository_kerberos"),
    url(r'^repository/kerberos/user_search_test/?$', kerberos_user_search_test, name="Kerberos user search test"),
    url(r'^repository/ldap/?$', LDAPRepositoryListView.as_view(), name="repository_ldap"),
    url(r'^repository/ldap/edit/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', LDAPRepositoryEditView.as_view(),
        name="repository_ldap"),
    url(r'^repository/ldap/clone/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', CloneView.as_view(),
        {'obj_type': LDAPRepository, 'name_attribute': 'repo_name', 'redirect_url': '/repository/ldap/'},
        name="repository_ldap"),
    url(r'^repository/ldap/delete/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', DeleteAuth.as_view(),
        {'obj_type': LDAPRepository, 'redirect_url': '/repository/ldap/', 'delete_url': '/repository/ldap/delete/'},
        name="repository_ldap"),
    url(r'^repository/ldap/connection_test/?$', ldap_connection_test, name="LDAP connection test"),
    url(r'^repository/ldap/user_search_test/?$', ldap_user_search_test, name="LDAP user search test"),
    url(r'^repository/ldap/group_search_test/?$', ldap_group_search_test, name="LDAP group search test"),
    url(r'^repository/radius/?$', RadiusRepositoryListView.as_view(), name="repository_radius"),
    url(r'^repository/radius/edit/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', RadiusRepositoryEditView.as_view(),
        name="repository_radius"),
    url(r'^repository/radius/clone/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', CloneView.as_view(),
        {'obj_type': RadiusRepository, 'name_attribute': 'repo_name', 'redirect_url': '/repository/radius/'},
        name="repository_radius"),
    url(r'^repository/radius/delete/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', DeleteAuth.as_view(),
        {'obj_type': RadiusRepository, 'redirect_url': '/repository/radius/',
         'delete_url': '/repository/radius/delete/'}, name="repository_radius"),
    url(r'^repository/radius/user_search_test/?$', radius_user_search_test, name="Radius user search test"),
    url(r'^repository/mongodb/?$', MongoDBRepositoryListView.as_view(), name="repository_mongodb"),
    url(r'^repository/mongodb/edit/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', MongoDBRepositoryEditView.as_view(),
        name="repository_mongodb"),
    url(r'^repository/mongodb/clone/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', CloneView.as_view(),
        {'obj_type': MongoDBRepository, 'name_attribute': 'repo_name', 'redirect_url': '/repository/mongodb/'},
        name="repository_mongodb"),
    url(r'^repository/mongodb/delete/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', DeleteAuth.as_view(),
        {'obj_type': MongoDBRepository, 'redirect_url': '/repository/mongodb/',
         'delete_url': '/repository/mongodb/delete/'}, name="repository_mongodb"),
    url(r'^repository/mongodb/connection_test/?$', mongodb_connection_test, name="MongoDB connection test"),
    url(r'^repository/mongodb/user_search_test/?$', mongodb_user_search_test, name="MongoDB user search test"),
    url(r'^repository/elasticsearch/connection_test/?$', elasticsearch_connection_test, name="ELastic connection test"),
    url(r'^repository/sso_profiles/?$', profile_list, name="sso profiles in mongodb"),
    url(r'^repository/sso_profiles/edit/(?P<app_id>[A-Fa-f0-9]{24})/(?P<login>.+)$', profile_edit, name="sso profiles in mongodb"),
    url(r'^repository/sso_profiles/delete/(?P<app_id>[A-Fa-f0-9]{24})/(?P<login>.+)$', DeleteSSOProfile.as_view(),
        name="repository_mongodb"),
    url(r'^repository/elasticsearch/?$', ElasticSearchRepositoryListView.as_view(), name="repository_elasticsearch"),
    url(r'^repository/elasticsearch/edit/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', ElasticSearchRepositoryEditView.as_view(),
        name="repository_elasticsearch_edit"),
    url(r'^repository/elasticsearch/clone/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', CloneView.as_view(),
        {'obj_type': ElasticSearchRepository, 'name_attribute': 'repo_name',
         'redirect_url': '/repository/elasticsearch/'}, name="repository_elasticsearch"),
    url(r'^repository/elasticsearch/delete/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', DeleteAuth.as_view(),
        {'obj_type': ElasticSearchRepository, 'redirect_url': '/repository/elasticsearch/',
         'delete_url': '/repository/elasticsearch/delete/'}, name="repository_elasticsearch"),
    url(r'^repository/otp/?$', OTPRepositoryListView.as_view(), name="repository_otp"),
    url(r'^repository/otp/edit/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', OTPRepositoryEditView.as_view(),
        name="repository_otp_edit"),
    url(r'^repository/otp/clone/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', CloneView.as_view(),
        {'obj_type': OTPRepository, 'name_attribute': 'repo_name', 'redirect_url': '/repository/otp/'},
        name="repository_otp"),
    url(r'^repository/otp/delete/(?P<object_id>[A-Fa-f0-9]{24}/?)?$', DeleteAuth.as_view(),
        {'obj_type': OTPRepository, 'redirect_url': '/repository/otp/', 'delete_url': '/repository/otp/delete/'},
        name="repository_otp"),

    # Cluster routes
    url(r'^cluster/$', general_settings, name="cluster_settings"),
    url(r'^cluster/manage/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', cluster_edit, name="cluster_settings"),
    url(r'^cluster/manage/promote/(?P<object_id>[A-Fa-f0-9]{24})?$', promote, name="cluster_settings"),
    url(r'^cluster/manage/remove/(?P<object_id>[A-Fa-f0-9]{24})?$', remove, name="cluster_settings"),
    url(r'^cluster/manage/join/(?P<object_id>[A-Fa-f0-9]{24})?$', join, name="cluster_settings"),
    url(r'^cluster/manage/redis-promote/(?P<object_id>[A-Fa-f0-9]{24})?$', redis_promote, name="cluster_settings"),
    url(r'^cluster/update/?$', update, name="cluster_settings"),
    url(r'^cluster/update/status/?$', need_update, name="cluster_settings"),
    url(r'^cluster/update/(?P<object_id>[A-Fa-f0-9]{24})/(?P<update_type>(?:engine)|(?:gui)|(?:libs))/?$',
        launch_update, name="cluster_settings"),
    url(r'^cluster/vulns/status/?$', check_vulns, name="cluster_settings"),
    url(r'^cluster/vulns/infos/(?P<object_id>[A-Fa-f0-9]{24})?$', get_vulns, name="cluster_settings"),
    url(r'^cluster/diagnostic/status/?$', check_diagnostic, name="cluster_settings"),
    url(r'^cluster/manage/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteNode.as_view(), name='cluster_settings'),

    # Service routes
    url(r'^services/ntp/(?P<object_id>[A-Fa-f0-9]{24})?$', ntp_view, name="service_settings"),
    url(r'^services/ntp/(?:(?P<object_id>[A-Fa-f0-9]{24})/)?restart/$', restart_ntp, name="service_settings"),
    url(r'^services/smtp/test/$', test_smtp, name="service_settings"),
    url(r'^services/dns/(?P<object_id>[A-Fa-f0-9]{24})?$', dns_view, name="service_settings"),
    url(r'^services/smtp/(?P<object_id>[A-Fa-f0-9]{24})?$', smtp_view, name="service_settings"),
    url(r'^services/global/$', global_view, name="service_settings"),
    url(r'^services/ssh/(?P<object_id>[A-Fa-f0-9]{24})?$', ssh_view, name="service_settings"),
    url(r'^services/ipsec/(?P<object_id>[A-Fa-f0-9]{24})?$', ipsec_view, name="service_settings"),
    url(r'^services/pf/(?P<object_id>[A-Fa-f0-9]{24})?$', pf_view, name="packetfilter"),
    url(r'^services/loganalyser/(?P<object_id>[A-Fa-f0-9]{24})?$', loganalyser_view, name="service_settings"),
    url(r'^services/pf/(?:(?P<object_id>[A-Fa-f0-9]{24})/)?restart/$', restart_pf, name="service_settings"),

    # PKI routes
    url(r'^system/cert/$', cert_list, name="cert_settings"),
    url(r'^system/cert/create$', create, name="cert_settings"),
    url(r'^system/cert/import$', load, name="cert_settings"),
    url(r'^system/cert/import-trusted-ca$', load_ca, name="cert_settings"),
    url(r'^system/cert/sign$', sign, name="cert_settings"),
    url(r'^system/cert/revoke/(?P<object_id>[A-Fa-f0-9]{24})?$', RevokeCertificate.as_view(), name="cert_settings"),
    url(r'^system/cert/download/(?P<object_id>[A-Fa-f0-9]{24})?$', cert_download, name="cert_settings"),
    url(r'^system/cert/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', cert_edit, name="cert_settings"),

    # Network routes
    url(r'^network/listeners/$', inet_list, name="network_settings"),
    url(r'^network/listeners/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', edit_inet, name="network_settings"),
    url(r'^network/listeners/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteListener.as_view(),
        name="network_settings"),
    url(r'^network/topology/$', topology, name="topology_settings"),
    url(r'^network/loadbalancer/$', loadbalancer, name="loadbalancer_settings"),
    url(r'^network/loadbalancer/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', edit_loadbalancer,
        name="loadbalancer_settings"),
    url(r'^network/loadbalancer/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteLoadBalancer.as_view(),
        name="loadbalancer_settings"),

    # ProxyBalancer routes
    url(r'^network/proxybalancer/$', proxybalancer_list, name="proxybalancer_settings"),
    url(r'^network/proxybalancer/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', proxybalancer_edit,
        name="proxybalancer_settings"),
    url(r'^network/proxybalancer/clone/(?P<object_id>[A-Fa-f0-9]{24})?$', proxybalancer_clone,
        name="proxybalancer_settings"),
    url(r'^network/proxybalancer/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteProxyBalancer.as_view(),
        name="proxybalancer_settings"),
    # Rewrite routes
    url(r'^network/rewrite/$', rewrite_list, name="rewrite_settings"),
    url(r'^network/rewrite/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', rewrite_edit, name="rewrite_settings"),
    url(r'^network/rewrite/clone/(?P<object_id>[A-Fa-f0-9]{24})?$', rewrite_clone, name="rewrite_settings"),
    url(r'^network/rewrite/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteRewrite.as_view(), name="rewrite_settings"),
    # Application routes
    url(r'^application/$', application_list, name="application_settings"),
    url(r'^application/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', application_edit, name="application_settings"),
    url(r'^application/clone/(?P<object_id>[A-Fa-f0-9]{24})?$', application_clone, name="application_settings"),
    url(r'^application/ssotest$', ssotest, name="application_settings"),
    url(r'^application/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteApplication.as_view(),
        name="application_settings"),
    url(r'^application/fetch_ldap_groups/(?P<object_id>[A-Fa-f0-9]{24})?$', fetch_ldap_groups,
        name="application_settings"),
    # Template routes
    url(r'^template/$', template_list, name="template_settings"),
    url(r'^template/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', template_edit, name="template_settings"),
    url(r'^template/clone/(?P<object_id>[A-Fa-f0-9]{24})?$', template_clone, name="template_settings"),
    url(r'^template/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeletePortalTemplate.as_view(), name="template_settings"),
    url(r'^template/image/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', image_edit, name="template_settings"),
    url(r'^template/image/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteImage.as_view(), name="template_settings"),

    # Management routes
    url(r'^management/reload/(?P<object_id>[A-Fa-f0-9]{24})?$', reload, name="template_settings"),
    url(r'^management/reloadapp/(?P<object_id>[A-Fa-f0-9]{24})?$', reloadapp, name="template_settings"),
    url(r'^management/reloadall$', reloadall, name="template_settings"),
    url(r'^management/startall$', startall, name="template_settings"),
    url(r'^management/stopall$', stopall, name="template_settings"),
    url(r'^management/start/(?P<object_id>[A-Fa-f0-9]{24})?$', start, name="template_settings"),
    url(r'^management/stop/(?P<object_id>[A-Fa-f0-9]{24})?$', stop, name="template_settings"),
    url(r'^management/download/(?P<object_id>[A-Fa-f0-9]{24})?$', conf_download, name="template_settings"),
    url(r'^management/status/(?P<object_id>[A-Fa-f0-9]{24})?$', status, name="template_settings"),
    url(r'^management/statusfull/(?P<object_id>[A-Fa-f0-9]{24})?$', statusfull, name="template_settings"),

    # ModAuth routes
    url(r'^firewall/access/$', access_list, name="modaccess_settings"),
    url(r'^firewall/access/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', access_edit, name="modaccess_settings"),
    url(r'^firewall/access/fetch_ldap_user/(?P<object_id>[A-Fa-f0-9]{24})?$', fetch_ldap_user,
        name="modaccess_settings"),
    url(r'^firewall/access/clone/(?P<object_id>[A-Fa-f0-9]{24})?$', access_clone, name="modaccess_settings"),
    url(r'^firewall/access/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteModAccess.as_view(),
        name="modaccess_settings"),

    # ModSecurity routes
    #url(r'^firewall/modsec/$', policy_list, name="waf_settings"),
    url(r'^firewall/modsec/$', policy_list, name="waf_settings"),
    url(r'^firewall/modsec/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', modsec_edit, name="waf_settings"),
    url(r'^firewall/modsec/clone/(?P<object_id>[A-Fa-f0-9]{24})?$', modsec_clone, name="waf_settings"),
    url(r'^firewall/modsec/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteModSec.as_view(), name="waf_settings"),
    url(r'^firewall/modsec_rules/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteModSecRulesSet.as_view(),
        name="waf_settings"),
    url(r'^firewall/modsec_rules/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteModSecRules.as_view(),
        name="waf_settings"),
    url(r'^firewall/modsec_rules/import_scan/$', import_scan, name="virtual_patching"),
    url(r'^firewall/virtualpatching/$', rulesset_list, {'type_modsec': 'virtualpatching'}, name="virtual_patching"),
    url(r'^firewall/blacklist/$', rulesset_list, {'type_modsec': 'blacklist'}, name="waf_rules_settings"),
    url(r'^firewall/whitelist/$', rulesset_list, {'type_modsec': 'whitelist'}, name="waf_rules_settings"),
    url(r'^firewall/modsec_rules/$', rulesset_list, {'type_modsec': 'crs/trustwave'}, name="waf_rules_settings"),
    url(r'^firewall/modsec_rules/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', edit_rules, name="waf_rules_settings"),
    url(r'^firewall/modsec_rules/editfile/(?P<object_id>[A-Fa-f0-9]{24})?$', edit_file, name="waf_rules_settings"),
    url(r'^firewall/modsec_rules/clone/(?P<object_id>[A-Fa-f0-9]{24})?$', clone_rules, name="waf_rules_settings"),
    url(r'^firewall/modsec_rules/import_crs/(?P<trustwave>[a-z]+)?$', import_crs, name="waf_rules_settings"),
    url(r'^firewall/modsec_rules/add_rules_wl_bl/?$', add_rules_wl_bl, name="waf_rules_settings"),
    url(r'^firewall/modsec_rules/get_rules_wl_bl/?$', get_rules_wl_bl, name="waf_rules_settings"),

    # ModLog routes
    url(r'^system/log/$', log_list, name="modlog_settings"),
    url(r'^system/log/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', log_edit, name="modlog_settings"),
    url(r'^system/log/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteModLog.as_view(), name="modlog_settings"),

    # Workers routes
    url(r'^system/worker/$', worker_list, name="worker_settings"),
    url(r'^system/worker/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', worker_edit, name="worker_settings"),
    url(r'^system/worker/clone/(?P<object_id>[A-Fa-f0-9]{24})?$', worker_clone, name="worker_settings"),
    url(r'^system/worker/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteWorker.as_view(), name="worker_settings"),

    # ModSSL routes
    url(r'^system/ssl/$', ssl_list, name="modssl_settings"),
    url(r'^system/ssl/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', modssl_edit, name="modssl_settings"),
    url(r'^system/ssl/clone/(?P<object_id>[A-Fa-f0-9]{24})?$', modssl_clone, name="modssl_settings"),
    url(r'^system/ssl/delete/(?P<object_id>[A-Fa-f0-9]{24})?$', DeleteModSSL.as_view(), name="modssl_settings"),

    # DataSet routes
    url(r'^datasets/$', datasets, name="dataset"),
    url(r'^dataset/add/$', dataset_add, name="dataset"),
    url(r'^dataset/list/$', dataset_list, name="dataset"),
    url(r'^dataset/get$', dataset_get, name="dataset"),
    url(r'^dataset/get_learning$', dataset_get_learning, name="dataset"),
    url(r'^dataset/build/(?P<object_id>[A-Fa-f0-9]{24})$', dataset_build, name="dataset"),
    url(r'^dataset/print_graph', print_graph, name="dataset"),
    url(r'^dataset/graph_realtime', graph_realtime, name="dataset"),
    url(r'^dataset/status$', dataset_status, name="dataset"),
    url(r'^dataset/logs/remove$', remove_logs, name="dataset"),
    url(r'^dataset/logs/remove_learning$', remove_logs_learning, name="dataset"),
    url(r'^dataset/delete/(?P<object_id>[A-Fa-f0-9]{24})$', DeleteDataset.as_view(), name="dataset"),
    url(r'^dataset/delete_learning/(?P<collection_name>\w+)$', delete_learning, name="dataset"),
    url(r'^dataset/edit/(?P<object_id>[A-Fa-f0-9]{24})?$', dataset_edit, name="dataset"),
    url(r'^dataset/edit_learning/(?P<collection_name>\w+)$', learning_edit, name="dataset"),
    url(r'^dataset/generate_wl/(?P<collection_name>\w+)$', generate_wl, name="dataset"),
    url(r'^dataset/add_wl/(?P<collection_name>\w+)?$', add_wl, name="dataset"),
    url(r'^svm/(?P<object_id>[A-Fa-f0-9]{24})?/charts$', svm_view, name="dataset"),

    # API routes
    url(r'^', include('api.urls')),
]
