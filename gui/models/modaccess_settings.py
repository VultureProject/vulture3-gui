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
__doc__ = 'Django models dedicated to Apache mod_access directives'

from django.utils.translation import ugettext_lazy as _
from mongoengine import DynamicDocument, PULL, ReferenceField, StringField


class AccessRule:
    def __init__(self):
        self.element = ''
        self.isnot = ''
        self.expected = ''



class ModAccess(DynamicDocument):
    """ Vulture mod_Access model representation
    name: A friendly name for the Access directives
    access_list: Allow from and Deny from directives
    """
    name = StringField(required=True,help_text=_('Friendly Name to reference the access list'))
    access_list = StringField(required=False,help_text=_('Define IPs or Hosts from which connection are allowed'))
    user_list=StringField(required=False)
    group_list=StringField(required=False)
    ldap_repo=ReferenceField('LDAPRepository', required=False, reverse_delete_rule=PULL)


    def get_user_list(self):
        """ Returns authorized users
        :param:
        """
        if not self.user_list:
            return ""
        ret = ""
        for s in self.user_list.split('|'):
            ret = ret + '"' + s + '",'
        return ret[:-1]

    def get_group_list(self):
        """ Returns authorized groups
        :param:
        """
        if not self.group_list:
            return ""
        ret = ""
        for s in self.group_list.split('|'):
            ret = ret + '"' + s + '",'
        return ret[:-1]

    """Build the Apache configuration
    """
    def getConf (self, br=None):

        ret=''
        for r in self.access_list.split('\n'):
            elt = r.split('|||')
            try:
                if str(elt[0]) == "":
                    continue

                if str(elt[0]) == "all-denied":
                    ret = ret + 'Require all denied'
                elif str(elt[0]) == "all-granted":
                    ret = ret + 'Require all granted'
                elif str(elt[0]) == "valid-user":
                    ret = ret + 'Require valid-user'
                else:
                    if str(elt[1]) == "isnot":
                        ret = ret + 'Require not ' + str(elt[0]) + ' '
                    else:
                        ret = ret + 'Require ' + str(elt[0]) + ' '


                if str(elt[2]) == "expr":
                    ret = ret + '"' + str(elt[2]) + '"\n'
                else:
                    ret = ret + str(elt[2]) + '\n'
                ret=ret+'\t    '
            except:
                continue

        if br:
            return ret.replace ('\n','<br>')
        return ret

    def __str__(self):
        return self.name
