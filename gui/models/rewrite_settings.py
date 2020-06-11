#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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
__doc__ = 'Django models dedicated to rewrite rules'


from django.utils.translation import ugettext_lazy as _
from mongoengine import StringField, BooleanField, ListField, ReferenceField, DynamicDocument, PULL

class RewriteRule (DynamicDocument):
    """ mod_rewrite Rule or Condition
    pattern: Pattern to match for rewriting / the test of the condition
    replacement: Pattern for replacement for rewriting / the expression to satisfy for the condition
    flags: Flags affecting the rule behaviour. If flag=='COND' then it is not a rule, but a condition
    """
    pattern = StringField(required=True)
    replacement = StringField(required=True)
    flags = StringField(required=True)


class Rewrite (DynamicDocument):
    """ mod_rewrite Rule
    name: Friendly name of the rule
    is_template: If True, the rule is a template and cannot be used in applications
    rules: The ruleset
    application: A reference to applications on witch to apply rules
    """
    name        = StringField(required=True, help_text=_('A friendly name for the ruleset'))
    is_template = BooleanField(required=False, help_text=_('Check for make thie rule a template'))
    rules       = ListField(ReferenceField('RewriteRule', reverse_delete_rule=PULL))
    application = ListField(ReferenceField('Application', reverse_delete_rule=PULL), help_text=_('If blank: Apply rule to all applications'))

    def applicationList(self):

        if not self.application:
            return '*'

        str = ''
        for app in self.application:
            str = str + "{}" .format(app.name + ' [ ' + app.type + ' ] <br>')
        return str

    def buildRules(self):
        if self.is_template:
            return ''

        str = ''
        tab = ''
        for rule in self.rules:
            if rule.flags == 'COND':
                str += tab + 'RewriteCond {}'.format(rule.pattern + ' ' + rule.replacement + '\n')
            elif rule.flags == "":
                str += tab + 'RewriteRule {}'.format(rule.pattern + ' ' + rule.replacement + '\n')
            else:
                str += tab + 'RewriteRule {}'.format(rule.pattern + ' ' + rule.replacement + ' [' + rule.flags + ']\n')
            tab = '    '

        return str

    def buildHTMLRules(self):

        buff = ''
        for rule in self.rules:
            if rule.flags == 'COND':
                buff += 'RewriteCond {}'.format(rule.pattern + ' ' + rule.replacement + '<br>')
            else:
                buff += '&nbsp;&nbsp;RewriteRule {}'.format(rule.pattern + ' ' + rule.replacement + ' [' + rule.flags + ']<br>')

        return buff
