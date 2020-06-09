from django.conf.urls import url

from api.views.cluster import node_configuration, node_initialization, node_status, node_upgrade, node_version, \
    update_replicalist, refresh_rc_conf, refresh_krb5_conf, refresh_portal_template_conf
from api.views.logs import check_status, get as get_logs
from api.views.network import up, down, running, start as net_start, stop as net_stop, reloadListener, need_restart, \
    status as net_status, statusfull as net_statusfull
from api.views.services import start, restart, stop, status, redis_master
from api.views.supervision import process_info, system_time_info, realtime
from api.views.application_rest_manager import get_all, generate, update, get_by_name, get_by_regex, delete, stats,\
    get_all_apps, get_all_models
from django.views.decorators.csrf import csrf_exempt

from api.views.certs import write_ca, remove_ca, remove_cert
from api.views.sso_profiles import SSOProfilesAPI
from api.views.repositories import RepositoriesAPI

urlpatterns = [
    # Cluster routes
    url(r'^api/cluster/node/new/$', node_configuration, name="Cluster Management"),
    url(r'^api/cluster/node/init/$', node_initialization, name="Cluster Management"),
    url(r'^api/cluster/node/status/$', node_status, name="Cluster Management"),
    url(r'^api/cluster/node/version/$', node_version, name="Cluster Management"),
    url(r'^api/cluster/replica/update/$', update_replicalist, name="Cluster Management"),
    url(r'^api/cluster/management/conf/$', refresh_rc_conf, name="Cluster Management"),
    url(r'^api/cluster/management/conf/krb5/$', refresh_krb5_conf, name="Cluster Management"),
    url(r'^api/cluster/management/conf/portal_template/(?P<template_id>[A-Fa-f0-9]{24})/?$',
        refresh_portal_template_conf, name="Cluster Management"),
    url(r'^api/cluster/update/(?P<update_type>(?:engine)|(?:gui)|(?:libs))/?$', node_upgrade,
        name="Cluster Management"),

    # Service routes,
    url(r'^api/services/(?P<service_name>[a-z0-9]{2,6})/start/$', start, name="Services Management"),
    url(r'^api/services/(?P<service_name>[a-z0-9]{2,6})/restart/$', restart, name="Services Management"),
    url(r'^api/services/(?P<service_name>[a-z0-9]{2,6})/stop/$', stop, name="Services Management"),
    url(r'^api/services/(?P<service_name>[a-z0-9]{2,6})/status/$', status, name="Services Management"),
    url(r'^api/services/redis/master/$', redis_master, name="Services Management"),

    # Network routes
    url(r'^api/network/listener/(?P<inet_id>[A-Fa-f0-9]{24})/up/$', up, name="Network Management"),
    url(r'^api/network/listener/(?P<inet_id>[A-Fa-f0-9]{24})/down/$', down, name="Network Management"),
    url(r'^api/network/listener/running/(?P<listener_id>[A-Fa-f0-9]{24})/(?P<port>[0-9]+)$', running,
        name="Network Management"),
    url(r'^api/network/listener/start/(?P<listenaddress_id>[A-Fa-f0-9]{24})$', net_start, name="Network Management"),
    url(r'^api/network/listener/stop/(?P<listenaddress_id>[A-Fa-f0-9]{24})$', net_stop, name="Network Management"),
    url(r'^api/network/listener/reloadlistener/(?P<listenaddress_id>[A-Fa-f0-9]{24})$', reloadListener,
        name="Network Management"),
    url(r'^api/network/listener/needrestart/(?P<listenaddress_id>[A-Fa-f0-9]{24})$', need_restart,
        name="Network Management"),
    url(r'^api/network/listener/status/(?P<listenaddress_id>[A-Fa-f0-9]{24})$', net_status, name="Network Management"),
    url(r'^api/network/listener/statusfull/(?P<listenaddress_id>[A-Fa-f0-9]{24})$', net_statusfull,
        name="Network Management"),

    # Supervision routes
    url(r'^api/supervision/process/$', process_info, name="Supervision"),
    url(r'^api/supervision/system_time/$', system_time_info, name="Supervision"),
    url(r'^api/supervision/realtime/$', realtime, name="Supervision"),

    # Log management routes
    url(r'^api/logs/management/$', check_status, name="Log management"),
    url(r'^api/logs/get/$', get_logs, name="Log management"),

    # Certificates routes
    url(r'api/certs/write_ca/(?P<cert_id>[A-Fa-f0-9]{24})$', write_ca, name="Certificates Management"),
    url(r'api/certs/remove_ca/(?P<cert_id>[A-Fa-f0-9]{24})$', remove_ca, name="Certificates Management"),
    url(r'api/certs/remove/(?P<cert_id>[A-Fa-f0-9]{24})$', remove_cert, name="Certificates Management"),

    # REST API - Application handling - <ROOT>/api/rest/app/<OPERATION>/<OPTIONS>/ #####################################
    # REST API - Application handling - Listing apps
    url(r'^api/rest/app/list/all/$', get_all, name='Application listing'),
    url(r'^api/rest/app/list/all/(?P<fields>[|\w]*)/$', get_all, name='Application listing'),
    url(r'^api/rest/app/list/application/$', get_all_apps, name='Application listing'),
    url(r'^api/rest/app/list/application/(?P<fields>[|\w]*)/$', get_all_apps, name='Application listing'),
    url(r'^api/rest/app/list/model/$', get_all_models, name='Application listing'),
    url(r'^api/rest/app/list/model/(?P<fields>[|\w]*)/$', get_all_models, name='Application listing'),

    # REST API - Application handling - Listing an app
    url(r'^api/rest/app/list/name/(?P<app_name>[\w #]*)/$', get_by_name, name='Application getter by name'),
    url(r'^api/rest/app/list/regex/(?P<regex>[\w #]*)/$', get_by_regex, name='Application getter by REGEX'),
    url(r'^api/rest/app/list/name/(?P<app_name>[\w #]*)/(?P<fields>[|\w]*)/$', get_by_name,
        name='Application getter by name'),
    url(r'^api/rest/app/list/regex/(?P<regex>[\w #]*)/(?P<fields>[|\w]*)/$', get_by_regex,
        name='Application getter by REGEX'),

    # REST API - Application handling - Generate / Update an app
    url(r'^api/rest/app/generate/$', generate, name='Application generation'),
    url(r'^api/rest/app/generate/(?P<is_reload>reload)/$', generate, name='Application generation'),
    url(r'^api/rest/app/update/(?P<app_name>[\w #]*)/$', update, name='Application updating'),
    url(r'^api/rest/app/delete/(?P<app_name>[\w #]*)/$', delete, name='Application deletion'),

    # REST API - Application handling - Stats & various
    url(r'^api/rest/app/stats/$', stats, name='Number of applications'),

    # REST API - SSO Profiles management
    url(r'^api/rest/sso_profiles/(?P<app_id>[A-Fa-f0-9]{24})(/?|/(?P<login>.+))$', csrf_exempt(SSOProfilesAPI.as_view()), name='SSO Profiles'),
    url(r'^api/rest/users/(?P<repo_id>[A-Fa-f0-9]{24})(/?|/(?P<login>.+))$', csrf_exempt(RepositoriesAPI.as_view()), name='SSO Profiles'),
]
