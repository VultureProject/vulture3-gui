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

import re

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def key(d, key_name):
    """ Tags used to access dict key from a variable

    :param d:
    :param key_name:
    :return:
    """
    return d[key_name]
key = register.filter('key', key)


@register.filter(name='mongoid')
def private(obj):
    return getattr(obj, 'id')


@register.filter(name='search')
def search(value, pattern):
    """
    Replace the searched pattern by a specific char sequence
    :param value: The string in which you "search"
    :param pattern: The substring you search
    :return: The modified value
    """
    return re.sub(pattern, '#f4x@SgXXmS', value)


@register.filter(name='replace')
def replace(value, pattern):
    """
    Replace the previously searched pattern by the patter you want
    :param value: The string previously "searched"
    :param pattern: The pattern you want to replace with
    :return: The modified value
    """
    return re.sub('#f4x@SgXXmS', pattern, value)
