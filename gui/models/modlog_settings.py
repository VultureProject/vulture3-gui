#!/usr/bin/python
# -*- coding: utf-8 -*-
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
__author__ = "Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django models dedicated to Apache Log file and log format'

from django.utils.translation import ugettext_lazy as _
from mongoengine import (BooleanField, DynamicDocument, DynamicField, EmbeddedDocument, IntField, ObjectIdField,
                         StringField)

from gui.signals.gui_signals import log_modified
from gui.models.repository_settings import BaseAbstractRepository
from gui.models.repository_settings import MongoDBRepository
from gui.models.repository_settings import ElasticSearchRepository


class ModLog(DynamicDocument):
    """ Vulture logformat model representation
    name:       A friendly name for the log format
    format:     Apache LogFormat Syntax
    buffered:   A boolean to buffer logs into memory before writing to disk.
                This can improve performance but may conduct to logfile loss
    repository_type: Type of repository where Vulture will send logs
    data_repository: Data repository choose
    """

    SEP_LIST = (
        ('space', '<whitespace>'),
        ('tab', '<tabulation>'),
        ('comma', ','),
        ('semicolon', ';'),
        ('underscore', '_'),
        ('minus', '-')
    )
    REPO_TYPE = (
        ('file', 'File'),
        ('data', 'Data repository'),
    )

    name = StringField(required=True, help_text=_('Friendly Name to reference log format'))
    format = StringField(required=True, default='%{app_name}e,%a,%l,%u,%t,%r,%>s,%b,%{Referer}i,%{User-agent}i,%I,%O,%D,%{COUNTRY_CODE}e,%{REPUTATION}e', help_text=_('The format of log files'))
    separator = StringField(choices=SEP_LIST, default='space', required=True, help_text=_('Choose the desired separator between fields (whitespace is the Apache default)'))
    buffered = BooleanField(required=False, default=False, help_text=_('If checked, Vulture will buffer logs into memory before writing on disk. This can improove performance but also conduct to data loss'))
    repository_type = StringField(choices=REPO_TYPE, default='file', required=True, help_text=_("Type of repository where Vulture will store logs"))
    data_repository = ObjectIdField()
    syslog_repository = ObjectIdField()

    def get_tags(self):
        ret = ""
        for s in self.format.split(','):
            ret = ret + '"' + s + '",'
        return ret[:-1]

    def get_format(self):

        """ Force static format for mongoDB and elasticsearch repositories """
        if self.repository_type=='data':
            repo = BaseAbstractRepository.search_repository(self.data_repository)
            if isinstance(repo, MongoDBRepository):
                return "@cee:{\\\"app_name\\\":\\\"%{app_name}e\\\",\\\"src_ip\\\":\\\"%a\\\",\\\"user\\\":\\\"%u\\\",\\\"time\\\":\\\"%{%Y-%m-%dT%H:%M:%S:%Z}t\\\",\\\"http_method\\\":\\\"%m\\\",\\\"requested_uri\\\":\\\"%U%q\\\",\\\"http_code\\\":%>s,\\\"incoming_protocol\\\":\\\"%H\\\",\\\"referer\\\":\\\"%{Referer}i\\\",\\\"user_agent\\\":\\\"%{User-agent}i\\\",\\\"size\\\":%B,\\\"bytes_received\\\":%I,\\\"bytes_sent\\\":%O,\\\"time_elapsed\\\":%D,\\\"country\\\":\\\"%{COUNTRY_CODE}e\\\",\\\"city\\\":\\\"%{CITY}e\\\",\\\"lat\\\":\\\"%{LATITUDE}e\\\",\\\"lon\\\":\\\"%{LONGITUDE}e\\\",\\\"reputation\\\":\\\"%{REPUTATION0}e,%{REPUTATION1}e,%{REPUTATION2}e,%{REPUTATION3}e,%{REPUTATION4}e\\\",\\\"owasp_top10\\\":\\\"%{owasp_top10}e\\\",\\\"reasons\\\":\\\"%{reasons}e\\\",\\\"threshold\\\":\\\"%{threshold}e\\\",\\\"score\\\":\\\"%{score}e\\\"}"
            elif isinstance(repo, ElasticSearchRepository):
                return "@cee:{\\\"app_name\\\":\\\"%{app_name}e\\\",\\\"src_ip\\\":\\\"%a\\\",\\\"user\\\":\\\"%u\\\",\\\"time\\\":\\\"%{%Y-%m-%dT%H:%M:%S%z}t\\\",\\\"http_method\\\":\\\"%m\\\",\\\"requested_uri\\\":\\\"%U%q\\\",\\\"http_code\\\":%>s,\\\"incoming_protocol\\\":\\\"%H\\\",\\\"referer\\\":\\\"%{Referer}i\\\",\\\"user_agent\\\":\\\"%{User-agent}i\\\",\\\"size\\\":%B,\\\"bytes_received\\\":%I,\\\"bytes_sent\\\":%O,\\\"time_elapsed\\\":%D,\\\"country\\\":\\\"%{COUNTRY_CODE}e\\\",\\\"city\\\":\\\"%{CITY}e\\\",\\\"lat\\\":\\\"%{LATITUDE}e\\\",\\\"lon\\\":\\\"%{LONGITUDE}e\\\",\\\"reputation\\\":\\\"%{REPUTATION0}e,%{REPUTATION1}e,%{REPUTATION2}e,%{REPUTATION3}e,%{REPUTATION4}e\\\",\\\"owasp_top10\\\":\\\"%{owasp_top10}e\\\",\\\"reasons\\\":\\\"%{reasons}e\\\",\\\"threshold\\\":\\\"%{threshold}e\\\",\\\"score\\\":\\\"%{score}e\\\"}"

        separators = {
            'space': ' ',
            'tab': '\t',
            'comma': ',',
            'semicolon': ';',
            'underscore': '_',
            'minus': '-'
        }
        sep = separators.get(self.separator, ' ')

        ret = ""
        for s in self.format.split(','):
            s = s.replace('%r', '\\"%r\\"')
            s = s.replace('%{Referer}i', '\\"%{Referer}i\\"')
            s = s.replace('%{User-agent}i', '\\"%{User-agent}i\\"')
            s = s.replace('%{app_name}e', '\\"%{app_name}e\\"')
            ret = ret + s + sep
        return ret[:-1]

    @property
    def repository(self):
        """ Property used to map repository field to Repository Object

        :return:
        """
        if self.repository_type == 'data':
            from gui.models.repository_settings import BaseAbstractRepository
            return BaseAbstractRepository.search_repository(self.data_repository)
        return self.repository_type

    def save(self, *args, **kwargs):

        """ Override save method to create logfiles hen needed
            if bootstrap is set to True, then don't send the
            log_modified signal. This is to avoid timeout
            at bootstrap time when trying to contact non-existing
            API (Vulture-GUI is not started yet at this time)
        """

        boot = kwargs.get('bootstrap') or False
        if boot is False:
            log_modified.send(sender=self.__class__)

        super(ModLog, self).save(*args, **kwargs)

    def is_deletable(self):
        """ Method used to know if Modlog object is used by an Application.
        If object is used, user can't delete Modlog

        :return: True if object is not used, False otherwise
        """
        from gui.models.application_settings import Application
        used = Application.objects(log_custom=self)
        if used:
            return False
        return True

    def __str__(self):
        if self.repository_type == 'data':
            return "{} ({})".format(self.name, self.repository)
        return self.name


class Logs(EmbeddedDocument):
    """ Logs object for MongoDB repository
    """
    _id                     = DynamicField()
    src_port                = IntField()
    auditLogTrailer         = DynamicField()
    response_headers        = DynamicField()
    dst_port                = IntField()
    response_status         = DynamicField()
    response_code           = IntField()
    server_protocol         = DynamicField()
    incoming_protocol       = DynamicField()
    event_timestamp         = DynamicField()
    request_headers         = DynamicField()
    src_ip                  = DynamicField()
    requested_uri           = DynamicField()
    http_method             = DynamicField()
    modsec_timestamp        = DynamicField()
    event_date_microseconds = DynamicField()
    time                    = DynamicField()
    dst_ip                  = DynamicField()
    event_date_milliseconds = DynamicField()
    unique_id               = DynamicField()
    event_date_seconds      = DynamicField()
    bytes_received          = DynamicField()
    bytes_sent              = DynamicField()
    app_name                = DynamicField()
    user                    = DynamicField()
    time_elapsed            = DynamicField()
    referer                 = DynamicField()
    user_agent              = DynamicField()
    http_code               = DynamicField()
    size                    = DynamicField()
    type_logs               = StringField()
    request_body            = DynamicField()
    ctx_geoip_src_ip        = DynamicField()
    ctx                     = DynamicField()
