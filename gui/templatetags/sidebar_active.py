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
__author__ = "Florian Hagniel"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = ''

import logging
import re

from django import template
from django.core.urlresolvers import reverse, NoReverseMatch
logger = logging.getLogger("debug")

register = template.Library()


@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname):
    try:
        pattern = '^' + reverse(pattern_or_urlname)
    except NoReverseMatch:
        pattern = pattern_or_urlname
    path = context['request'].path
    if re.search(pattern, path):
        return 'active'
    return ''

@register.simple_tag(takes_context=True)
def active_parent(context, args):
    found = False
    for pattern_or_urlname in args.split(','):
        pattern_or_urlname = pattern_or_urlname.strip()
        try:
            pattern = '^' + reverse(pattern_or_urlname)
        except NoReverseMatch:
            pattern = pattern_or_urlname
        path = context['request'].path
        if re.search(pattern, path):
            found = True
    if found:
        return 'active-parent active'
    else:
        return ''


@register.simple_tag(takes_context=True)
def display_active(context, args):
    found = False
    for pattern_or_urlname in args.split(','):
        pattern_or_urlname = pattern_or_urlname.strip()
        try:
            pattern = '^' + reverse(pattern_or_urlname)
        except NoReverseMatch:
            pattern = pattern_or_urlname
        path = context['request'].path
        if re.search(pattern, path):
            found = True
    if found:
        return 'block'
    else:
        return 'none'