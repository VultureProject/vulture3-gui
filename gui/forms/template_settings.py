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
__doc__ = 'Django forms dedicated to template settings'

from django.forms import TextInput
from mongodbforms import DocumentForm

from gui.forms.forms_utils import bootstrap_tooltips
from gui.models.template_settings import portalTemplate, TemplateImage


class portalTemplateForm(DocumentForm):
    """ Application form representation
    """

    def __init__(self, *args, **kwargs):
        super(portalTemplateForm, self).__init__(*args, **kwargs)
        self = bootstrap_tooltips(self)

    class Meta:
        document = portalTemplate
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'html_login': TextInput(attrs={'class': 'form-control'}),
            'html_logout': TextInput(attrs={'class': 'form-control'}),
            'html_learning': TextInput(attrs={'class': 'form-control'}),
            'html_self': TextInput(attrs={'class': 'form-control'}),
            'html_password': TextInput(attrs={'class': 'form-control'}),
            'html_lost': TextInput(attrs={'class': 'form-control'}),
            'html_otp': TextInput(attrs={'class': 'form-control'}),
            'html_message': TextInput(attrs={'class': 'form-control'}),
            'html_error': TextInput(attrs={'class': 'form-control'}),
            'html_error_403': TextInput(attrs={'class': 'form-control'}),
            'html_error_404': TextInput(attrs={'class': 'form-control'}),
            'html_error_405': TextInput(attrs={'class': 'form-control'}),
            'html_error_406': TextInput(attrs={'class': 'form-control'}),
            'html_error_500': TextInput(attrs={'class': 'form-control'}),
            'html_error_501': TextInput(attrs={'class': 'form-control'}),
            'html_error_502': TextInput(attrs={'class': 'form-control'}),
            'html_error_503': TextInput(attrs={'class': 'form-control'}),
            'html_error_504': TextInput(attrs={'class': 'form-control'}),
            'css': TextInput(attrs={'class': 'form-control'}),
            'email_subject': TextInput(attrs={'class': 'form-control'}),
            'email_body': TextInput(attrs={'class': 'form-control'}),
            'email_from': TextInput(attrs={'class': 'form-control'}),
            'error_password_change_ok': TextInput(attrs={'class': 'form-control'}),
            'error_password_change_ko': TextInput(attrs={'class': 'form-control'}),
            'error_email_sent': TextInput(attrs={'class': 'form-control'}),
            'html_registration': TextInput(attrs={'class': 'form-control'}),
            'email_register_subject': TextInput(attrs={'class': 'form-control'}),
            'email_register_from': TextInput(attrs={'class': 'form-control'}),
            'email_register_body': TextInput(attrs={'class': 'form-control'}),

            'login_login_field': TextInput(attrs={'class': 'form-control'}),
            'login_password_field': TextInput(attrs={'class': 'form-control'}),
            'login_captcha_field': TextInput(attrs={'class': 'form-control'}),
            'login_submit_field': TextInput(attrs={'class': 'form-control'}),
            'learning_submit_field': TextInput(attrs={'class': 'form-control'}),
            'password_old_field': TextInput(attrs={'class': 'form-control'}),
            'password_new1_field': TextInput(attrs={'class': 'form-control'}),
            'password_new2_field': TextInput(attrs={'class': 'form-control'}),
            'password_email_field': TextInput(attrs={'class': 'form-control'}),
            'password_submit_field': TextInput(attrs={'class': 'form-control'}),
            'otp_key_field': TextInput(attrs={'class': 'form-control'}),
            'otp_submit_field': TextInput(attrs={'class': 'form-control'}),
            'otp_resend_field': TextInput(attrs={'class': 'form-control'}),
            'otp_onetouch_field': TextInput(attrs={'class': 'form-control'}),
            'register_captcha_field': TextInput(attrs={'class': 'form-control'}),
            'register_username_field': TextInput(attrs={'class': 'form-control'}),
            'register_phone_field': TextInput(attrs={'class': 'form-control'}),
            'register_password1_field': TextInput(attrs={'class': 'form-control'}),
            'register_password2_field': TextInput(attrs={'class': 'form-control'}),
            'register_email_field': TextInput(attrs={'class': 'form-control'}),
            'register_submit_field': TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        super(portalTemplateForm, self).clean()

        return self.cleaned_data


class TemplateImageForm(DocumentForm):
    """ Image insertion form représentation
    """

    class Meta:
        document = TemplateImage
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
        }
