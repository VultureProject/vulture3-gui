# -*- coding: utf-8 -*-
from django.conf.urls import url

# Needed by handle_disconnect : Crash otherwise
from gui.models.user_document import VultureUser
from portal.views.disconnect import handle_disconnect
from portal.views.logon import log_in
from portal.views.oauth2_portal import log_in as oauth2_log_in, is_valid_token
from portal.views.portal_statics import template_image
from portal.views.register import registration
from portal.views.self import self as portal_self

urlpatterns = [
    ##############################-PORTAL ROUTES-##################################

    # Self-Service
    url(r'^portal/(?P<token_name>[A-Za-z0-9]+)/self/(?P<proxy_app_id>[A-Za-z0-9]+)$', portal_self, name="Self-Service"),
    url(r'^portal/(?P<token_name>[A-Za-z0-9]+)/self/(?P<action>[a-z]+)/(?P<proxy_app_id>[A-Za-z0-9]+)$', portal_self,
        name="Self-Service"),

    # Registration & login
    url(r'^portal/(?P<token_name>[A-Za-z0-9]+)/register/(?P<proxy_app_id>[A-Za-z0-9]+)$', registration, name="Log in"),
    url(r'^portal/(?P<token_name>[A-Za-z0-9]+)/(?P<token>[A-Za-z0-9]+)/(?P<proxy_app_id>[A-Za-z0-9]+)$', log_in,
        name="Log in"),
    url(r'^portal/2fa/otp', log_in),

    # OAuth2
    url(r'^portal/_oauth2/_login', oauth2_log_in, name="OAuth2"),
    url(r'^portal/_oauth2/_token', is_valid_token, name="OAuth2"),

    # Logout
    url(r'^portal/disconnect/(?P<app_id>[A-Za-z0-9]+)$', handle_disconnect, name="Disconnect"),

    # Templates
    url(r'^portal/[A-Za-z0-9]+/portal_statics/(?P<image_id>[A-Za-z0-9]+)?/[A-Za-z0-9]+', template_image,
        name="Template"),
]
