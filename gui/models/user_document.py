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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django models dedicated to user management'

from mongoengine import PULL
from mongoengine.django.auth import User, Group
from mongoengine.fields import ListField, ReferenceField, StringField, Document

from vulture_toolkit.auth.session import MongoSession


class VultureUser(User, Document):
    groups = ListField(ReferenceField('Group', reverse_delete_rule=PULL))
    auth_backend = StringField()

    def is_member_of(self, group_list):
        """ Method used to know if User is member of a group

        :param group_list: List of Group Object
        :return:
        """
        for grp in group_list:
            if grp in self.groups:
                return True
        return False

    def is_application_manager(self):
        if self.is_superuser:
            return True
        app_manager_grp = Group.objects.get(name='application_manager')
        return self.is_member_of([app_manager_grp])

    def is_security_manager(self):
        if self.is_superuser:
            return True
        sec_manager_grp = Group.objects.get(name='security_manager')
        return self.is_member_of([sec_manager_grp])

    def is_system_manager(self):
        if self.is_superuser:
            return True
        sys_manager_grp = Group.objects.get(name='system_manager')
        return self.is_member_of([sys_manager_grp])


    def nb_session(self):
        """Method used to count the number of entries in Session collection
        :return: number of connected user
        """
        return len(MongoSession.objects())


    def is_administrator(self):
        """Method used to know if user is in Administrator group

        :return: True if self is administrator member, False otherwise
        """
        if self.is_superuser:
            return True
        from mongoengine.django.auth import Group
        adm_grp = Group.objects.get(name='administrator')
        return self.is_member_of([adm_grp])

    meta = {
        'allow_inheritance': True,
        'indexes': [
            {'fields': ['username', 'auth_backend'], 'unique': True, 'sparse': False}
        ]
    }