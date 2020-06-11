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
__doc__ = 'Django views dedicated to Vulture GUI Cluster page'

from bson.objectid import ObjectId
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from gui.decorators import group_required


class DeleteView(View):
    template_name = 'generic_delete.html'
    menu_name = _("")
    obj = None
    redirect_url = ""
    delete_url = ""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DeleteView, self).dispatch(*args, **kwargs)

    def get(self, request, object_id, **kwargs):
        obj_inst = self.obj.objects.with_id(ObjectId(object_id))
        if not obj_inst:
            return HttpResponseForbidden("Injection detected.")
        return render_to_response(self.template_name,
                                  {'object_id': object_id,
                                   'menu_name': self.menu_name,
                                   'delete_url': self.delete_url,
                                   'redirect_url': self.redirect_url,
                                   'obj_inst': obj_inst},
                                  context_instance=RequestContext(request))

    def post(self, request, object_id, **kwargs):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            obj_inst.delete()
        return HttpResponseRedirect(self.redirect_url)


class RepositoryEditView(View):
    template_name = 'generic_repository.html'
    menu_name = _("")

    @method_decorator(group_required('administrator', 'application_manager'))
    def dispatch(self, *args, **kwargs):
        return super(RepositoryEditView, self).dispatch(*args, **kwargs)

    def get(self, request, object_id):
        instance = None
        if object_id:
            instance = self.obj.objects.with_id(ObjectId(object_id))
        form = self.form(instance=instance)
        return render_to_response(self.template_name,
                                  {'form': form, 'object_id': object_id},
                                  context_instance=RequestContext(request))

    def post(self, request, object_id):
        instance = None
        if object_id:
            instance = self.obj.objects.with_id(ObjectId(object_id))

        form = self.form(request.POST or None, instance=instance)

        if form.is_valid():
            try:
                instance=form.save(commit=False)
            except ValidationError as e:
                form.add_error('es_host', e[0])
                return render_to_response(self.template_name,
                                    {'form': form, 'object_id': object_id},
                                    context_instance=RequestContext(request))
            instance.save()
            return HttpResponseRedirect(self.redirect_url)
        else:
            return render_to_response(self.template_name,
                                      {'form': form, 'object_id': object_id},
                                      context_instance=RequestContext(request))


class CloneView(View):

    #FIXME Check decorators
    @method_decorator(group_required('administrator', 'application_manager'))
    def dispatch(self, *args, **kwargs):
        return super(CloneView, self).dispatch(*args, **kwargs)

    def get(self, request, object_id, obj_type, name_attribute, redirect_url):
        """ Generic view used to clone an Document object

        :param request: Django request object
        :param object_id: Objectid of Object to clone
        :param obj_type: Type of object (ex:SQLRepository)
        :param name_attribute: Name of 'name' attribute of object (ex: 'repo_name')
        :param redirect_url: Redirection URL
        :return: HTTPResponseRedirect to redirect_url
        """
        instance = None
        if object_id:
            instance = obj_type.objects.with_id(ObjectId(object_id))
            instance.pk = None
            obj_name = getattr(instance, name_attribute)
            obj_name = 'Copy of {}'.format(obj_name)
            setattr(instance, name_attribute, obj_name)
            instance.save()
        return HttpResponseRedirect(redirect_url)