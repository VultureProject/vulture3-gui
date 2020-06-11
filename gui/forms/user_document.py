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
__doc__ = 'Django forms dedicated to admin'

from django.forms import PasswordInput, CharField, SelectMultiple
from django.utils.translation import ugettext_lazy as _
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.user_document import VultureUser


class VultureUserForm(DocumentForm):
    """ Django form used to handle User edition
    """

    def __init__(self, *args, **kwargs):
        super(VultureUserForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self, exclude='password')
        instance = getattr(self, 'instance', None)
        # We can't change password for an external authentication backend
        if instance and type(instance.pk) is not property \
                and instance.auth_backend:
            self.fields['password'].widget.attrs['readonly'] = True
            self.fields['pwd_confirm'].widget.attrs['readonly'] = True

    pwd_confirm = CharField(label=_("Password confirmation"), required=False,
                            widget=PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        super(VultureUserForm, self).clean()
        pwd = self.cleaned_data.get('password')
        pwd_confirm = self.cleaned_data.get('pwd_confirm')
        # if password is not None, we got a password reset
        if pwd:
            if pwd != pwd_confirm:
                error = _('Password and password confirm fields mismatch')
                self._errors['password'] = error
                self._errors['pwd_confirm'] = error
            else:
                # Password and confirmation match, we can hash it before save it
                from django.contrib.auth.hashers import make_password
                self.cleaned_data['password'] = make_password(pwd)
        else:
            # Password isn't set, we take old value
            self.cleaned_data['password'] = self.instance.password

        return self.cleaned_data

    def clean_password(self):
        instance = getattr(self, 'instance', None)
        if instance and type(instance.pk) is not property \
                and instance.auth_backend:
            return None
        else:
            return self.cleaned_data['password']

    class Meta:
        document = VultureUser
        fields = ('password', 'pwd_confirm', 'groups', 'is_superuser')
        widgets = {
            'password': PasswordInput(attrs={'class': 'form-control'}),
            'groups': SelectMultiple(attrs={'class': 'form-control'}),
        }


class VultureNewUserForm(VultureUserForm):

    def clean_username(self):
        """ Username validation, it consists to ensure username is unique for
        Vulture internal backend

        :return:
        """
        username = self.cleaned_data.get('username')
        if username:
            try:
                VultureUser.objects.get(username=username, auth_backend=None)
                self._errors['username'] = _('This username already exist')
            except VultureUser.DoesNotExist:
                pass
        return username

    class Meta(VultureUserForm.Meta):
        fields = ('username', 'password', 'pwd_confirm', 'groups', 'is_superuser')