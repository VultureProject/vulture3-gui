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
__doc__ = 'Django views dedicated to URL rewriting rules'

import re

from bson.objectid import ObjectId
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from gui.decorators import group_required
from gui.forms.rewrite_settings import RewriteForm
from gui.models.rewrite_settings import Rewrite, RewriteRule
from gui.signals.gui_signals import config_modified


@group_required('administrator', 'application_manager')
def rewrite_list(request):
    """ Page dedicated to show rewriting rules list
    """
    try:
        rewrites = Rewrite.objects()
    except DoesNotExist:
        rewrites = None

    return render_to_response('rewrite.html', {'rewrites': rewrites}, context_instance=RequestContext(request))

@group_required('administrator', 'application_manager')
def clone(request, object_id=None):

    """ View dedicated to rewrite rules cloning
    :param object_id: MongoDB object_id of rewrite policy
    :param request: Django request object
    """
    # Retrieve rewrite configuration
    rewrite = Rewrite.objects.with_id(ObjectId(object_id))
    rules = rewrite.rules
    applications = rewrite.application

    # Clone rules
    rules_list = list()
    for r in rules:
        r.pk = None
        r.save()
        rules_list.append(r)

    # Clone rewrite policy
    rewrite.pk = None
    rewrite.name = 'Copy Of ' + str(rewrite.name)
    rewrite.is_template=False
    rewrite.rules=rules_list
    rewrite.application=applications
    rewrite.save()
    return HttpResponseRedirect('/network/rewrite/')

@group_required('administrator', 'application_manager')
def edit(request, object_id=None):

    """ View dedicated to rewriting rules management

    :param object_id: MongoDB object_id of a rule
    :param request: Django request object
    """
    # Retrieving rewriting configuration
    rewrite = Rewrite.objects.with_id(ObjectId(object_id))

    # Rewrite doesn't exist ==> create it
    if not rewrite:
        rewrite = Rewrite(name="My rule", is_template=False)

    # Check if rules are valid - and populate an array
    ruleset = []

    form = RewriteForm(request.POST or None, instance=rewrite)

    if request.method == 'POST':

        dataPosted      = request.POST
        dataPostedRaw   = str(request.body).split("&")
        for data in dataPostedRaw:

            m = re.match('pattern_(\d+)',data)
            if m is not None:
                id_ = m.group(1)

                # Force harmless default values to prevent any injection or jQuery problem
                pattern = '^/(.*)$'
                replacement = '/test/$1'
                flags = 'R'

                try:
                    pattern     = dataPosted['pattern_' + id_]
                    replacement = dataPosted['replacement_' + id_]
                    flags       = dataPosted['flags_' + id_]
                except Exception as e:
                    pass

                # FIXME: Coherence control
                rule = RewriteRule (pattern, replacement, flags)
                ruleset.append(rule)
    else:
        ruleset = rewrite.rules

    reload_needed = False
    # Saving information into database and redirect to rewrite list
    if request.method == 'POST' and form.is_valid():

        old_rewrite = Rewrite.objects.with_id(ObjectId(object_id))

        rewrite = form.save(commit=False)

        # If there is no old RewriteRule
        if not old_rewrite:
            reload_needed = True
        else:
            if len(ruleset) != len(old_rewrite.rules):
                reload_needed = True
            elif rewrite.pk != old_rewrite.pk \
                    or rewrite.name != old_rewrite.name \
                    or rewrite.is_template != old_rewrite.is_template \
                    or rewrite.application != old_rewrite.application:
                reload_needed = True
            else:
                i = 0
                for rule in ruleset:
                    if old_rewrite.rules[i].pattern != rule.pattern or \
                                    old_rewrite.rules[i].replacement != rule.replacement or \
                                    old_rewrite.rules[i].flags != rule.flags:
                        reload_needed = True
                        break
                    i += 1

        if reload_needed:
            # 1) Remove old rules
            if old_rewrite and old_rewrite.rules:
                for rule in old_rewrite.rules:
                    rule.delete()

            # 2) Create new rules
            for rule in ruleset:
                rule.save()

            # 3) Assign rules
            rewrite.rules = ruleset

            # 4) Save rewriting
            rewrite.save()
            config_modified.send(sender=Rewrite, id=rewrite.id)

        if reload_needed:
            return HttpResponseRedirect('/network/rewrite/#reload')
        else:
            return HttpResponseRedirect('/network/rewrite/')


    return render_to_response('rewrite_edit.html',
                              {'form':form, 'object_id': object_id,
                               'rulename':rewrite.name, 'ruleset':ruleset},
                              context_instance=RequestContext(request))


