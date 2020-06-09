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

import os

from bson.objectid import ObjectId

from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from gui.models.application_settings import Application, ListenAddress, ProxyBalancer
from gui.models.network_settings import Interface, Loadbalancer, LoadbalancerBackend, Listener
from gui.models.worker_settings import Worker
from gui.models.rewrite_settings import Rewrite
from gui.models.modaccess_settings import ModAccess
from gui.models.modlog_settings import ModLog
from gui.models.modssl_settings import ModSSL
from gui.models.modsec_settings import ModSec, ModSecRulesSet, ModSecRules
from gui.models.ssl_certificate import SSLCertificate
from gui.models.system_settings import Node
from gui.models.template_settings import portalTemplate, TemplateImage
from gui.models.repository_settings import SSOProfile
from gui.views.generic_views import DeleteView
from gui.models.dataset_settings import Dataset, SVM

import sys
import logging

sys.path.append('/home/vlt-gui/vulture')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vulture.settings")
logger = logging.getLogger('gui')


__author__ = "Florian Hagniel, Thomas Carayol, Hubert Loiseau"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to Vulture GUI Cluster page'


class DeleteSSOProfile(DeleteView):
    """Class dedicated to delete view of SSOProfile object

    """
    menu_name = _("Repositories -> SSO Profiles")
    obj = SSOProfile
    redirect_url = "/repository/sso_profiles/"
    delete_url = "/repository/sso_profiles/delete/"

    def get(self, request, app_id, login):
        obj_inst = Application.objects.with_id(ObjectId(app_id))
        if not obj_inst:
            return HttpResponseForbidden("Injection detected.")
        return render_to_response(self.template_name,
                                  {'object_id': "",
                                   'menu_name': self.menu_name,
                                   'delete_url': "",
                                   'redirect_url': self.redirect_url,
                                   'obj_inst': "SSO Profile (app={},login={})".format(obj_inst.name, login)},
                                  context_instance=RequestContext(request))

    def post(self, request, app_id, login):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            app = Application.objects.with_id(ObjectId(app_id))
            if not app:
                return HttpResponseForbidden("Injection detected.")
            app.delete_sso_profile(login)
            return HttpResponseRedirect(self.redirect_url)


class DeleteNode(DeleteView):
    """Class dedicated to delete view of Node object

    """
    menu_name = _("System Settings -> Cluster -> Manage Nodes -> Delete")
    obj = Node
    redirect_url = "/cluster/"
    delete_url = "/cluster/manage/delete/"

    def get(self, request, object_id):
        obj = self.obj.objects.with_id(ObjectId(object_id))
        if not obj:
            return HttpResponseForbidden("Injection detected.")

        for listener in obj.get_listeners():
            if listener.is_carp:
                self.template_name = "generic_delete_forbidden.html"
                break

            for la in ListenAddress.objects():
                if la.address == listener:
                    self.template_name = "generic_delete_forbidden.html"
                    break

            for lb in Loadbalancer.objects():
                if listener.ip == lb.incoming_listener.ip:
                    self.template_name = "generic_delete_forbidden.html"
                    break

        return super(DeleteNode, self).get(request, object_id)

    # TODO Method post
    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == "yes":
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            obj_inst.delete()
            return HttpResponseRedirect(self.redirect_url)


class DeleteModAccess(DeleteView):
    """Class dedicated to delete view of mod_access object

    """
    menu_name = _("Web Firewall -> Access Control -> Delete")
    obj = ModAccess
    redirect_url = "/firewall/access/"
    delete_url = "/firewall/access/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            obj_inst.delete()
            return HttpResponseRedirect(self.redirect_url)


class DeleteModSec(DeleteView):
    """Class dedicated to delete view of mod_security object

    """
    menu_name = _("Web Firewall -> ModSecurity -> Delete")
    obj = ModSec
    redirect_url = "/firewall/modsec/"
    delete_url = "/firewall/modsec/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')

        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            app_list = Application.objects(modsec_policy=obj_inst)

            if not len(app_list):
                obj_inst.delete()

            return HttpResponseRedirect(self.redirect_url)


class DeletePortalTemplate(DeleteView):
    """Class dedicated to delete view of mod_security object

    """
    menu_name = _("Template -> Delete")
    obj = portalTemplate
    redirect_url = "/template/"
    delete_url = "/template/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            obj_inst.delete()
            return HttpResponseRedirect(self.redirect_url)


class DeleteModSecRulesSet(DeleteView):
    """Class dedicated to delete view of mod_security rules set object

    """
    menu_name = _("Web Firewall -> ModSecurity -> Rules Set -> Delete")
    obj = ModSecRulesSet
    redirect_url = "javascript:window.history.back();"
    delete_url = "/firewall/modsec_rules/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden('Injection detected.')

            # Destroy all related rules in DB
            rules = ModSecRules.objects.filter(rs=obj_inst)
            for rule in rules:
                rule.delete()

            # Then destroy object
            obj_inst.delete()
            self.redirect_url = "/firewall/modsec_rules"
            if obj_inst.type_rule == 'virtualpatching':
                self.redirect_url = "/firewall/virtualpatching"

            return HttpResponseRedirect(self.redirect_url)


class DeleteModSecRules(DeleteView):
    """Class dedicated to delete a modsec rules object
    """
    menu_name = _("Web Firewall -> ModSecurity -> Rules Set -> Delete")
    obj = ModSecRules
    redirect_url = "javascript:window.history.back();"
    delete_url = "/firewall/modsec_rules/delete/"

    def post(self, request, object_id):
        if request.POST.get('confirm') == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            rs = ModSecRulesSet.objects.with_id(ObjectId(obj_inst.rs.id))

            obj_inst.delete()

            self.redirect_url = "/firewall/modsec_rules"
            if rs.type_rule == 'virtualpatching':
                self.redirect_url = "/firewall/virtualpatching"

            json = request.POST.get('json')
            if json:
                return JsonResponse({'status': True})

            return HttpResponseRedirect(self.redirect_url)


class RevokeCertificate(DeleteView):
    """Class dedicated to certificate revocation

    """
    menu_name = _("System Settings -> Certificate -> Revoke")
    obj = SSLCertificate
    redirect_url = "/system/cert/"
    delete_url = "/system/cert/revoke/"

    def get(self, request, object_id):
        obj = self.obj.objects.with_id(ObjectId(object_id))
        if not obj:
            return HttpResponseForbidden("Injection detected.")

        for modssl in ModSSL.objects.all():
            if obj == modssl.certificate:
                # Listener is used in an haproxy conf -> Forbidden delete
                self.template_name = 'generic_delete_forbidden.html'

        return super(RevokeCertificate, self).get(request, object_id)

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))

            obj_inst.revoke()

            return HttpResponseRedirect(self.redirect_url)


class DeleteProxyBalancer(DeleteView):
    """Class dedicated to delete view of mod_balancer object

    """
    menu_name = _("Application -> ProxyBalancer -> Delete")
    obj = ProxyBalancer
    redirect_url = "/network/proxybalancer/"
    delete_url = "/network/proxybalancer/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            # Delete orphan members
            for member in obj_inst.members:
                member.delete()
            obj_inst.delete()
            return HttpResponseRedirect(self.redirect_url)


class DeleteModLog(DeleteView):
    """Class dedicated to delete view of mod_log object

    """
    menu_name = _("System Settings -> Log Formats -> Delete")
    obj = ModLog
    redirect_url = "/system/log/"
    delete_url = "/system/log/delete/"

    def get(self, request, object_id):
        obj_inst = self.obj.objects.with_id(ObjectId(object_id))
        if not obj_inst:
            return HttpResponseForbidden("Injection detected.")
        if Application.objects(log_custom=obj_inst):
            self.template_name = 'generic_delete_forbidden.html'
        return super(DeleteModLog, self).get(request, object_id)

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            # Check if ModLog Object is not used by an Application
            if not Application.objects(log_custom=obj_inst):
                obj_inst.delete()
            else:
                pass
            return HttpResponseRedirect(self.redirect_url)


class DeleteModSSL(DeleteView):
    """Class dedicated to delete view of mod_ssl object

    """
    menu_name = _("System Settings -> SSL Profiles -> Delete")
    obj = ModSSL
    redirect_url = "/system/ssl/"
    delete_url = "/system/ssl/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            obj_inst.delete()
            return HttpResponseRedirect(self.redirect_url)


class DeleteWorker(DeleteView):
    """Class dedicated to delete view of Worker object

    """
    menu_name = _("Workers Settings -> Manage workers -> Delete")
    obj = Worker
    redirect_url = "/system/worker/"
    delete_url = "/system/worker/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            obj_inst.delete()
            return HttpResponseRedirect(self.redirect_url)


class DeleteApplication(DeleteView):
    """Class dedicated to delete view of Application object

    """
    menu_name = _("Application -> Delete")
    obj = Application
    redirect_url = "/application/"
    delete_url = "/application/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            app = self.obj.objects.with_id(ObjectId(object_id))
            if not app:
                return HttpResponseForbidden("Injection detected.")
            app.destroy()

            return HttpResponseRedirect(self.redirect_url)


class DeleteRewrite(DeleteView):
    """Class dedicated to delete view of Rewrite object

    """
    menu_name = _("URL Rewriting -> Delete")
    obj = Rewrite
    redirect_url = "/network/rewrite/"
    delete_url = "/network/rewrite/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            # Delete orphan rules
            for rule in obj_inst.rules:
                rule.delete()
            # Delete rewrite
            obj_inst.delete()
            return HttpResponseRedirect(self.redirect_url)


class DeleteListener(DeleteView):
    """Class dedicated to delete view of Listener object

    """
    menu_name = _("Listener -> Delete")
    obj = Listener
    redirect_url = "/network/listeners/"
    delete_url = "/network/listeners/delete/"

    def get(self, request, object_id):
        obj = self.obj.objects.with_id(ObjectId(object_id))
        if not obj:
            return HttpResponseForbidden("Injection detected.")
        for loadbalancer in Loadbalancer.objects.all():
            if obj == loadbalancer.incoming_listener:
                # Listener is used in an haproxy conf -> Forbidden delete
                self.template_name = 'generic_delete_forbidden.html'

        return super(DeleteListener, self).get(request, object_id)

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':

            """ Before deleting the listener: shutdown it and
            refresh rc.conf.local on the related node """
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            if obj_inst.is_carp:
                # Object is carp, need to iterate on each listener
                inet_carp = obj_inst.get_related_carp_inets()
                # intfs = Interface.objects.filter(
                # inet_addresses__in=[x.id for x in inet_carp])

                for inet in inet_carp:
                    intf = Interface.objects.get(inet_addresses__in=[inet])
                    node = Node.objects.get(interfaces=intf)
                    logger.info("Shutdown device {} on node {}".format(
                        intf.device, node.name))
                    res = node.api_request(
                        "/api/network/listener/" + str(inet.id) + "/down/")
                    logger.debug(res)

                    inet.delete(bootstrap=True)

                    # Then refresh rc_conf
                    logger.info("Refresh rc_conf on node {}".format(node.name))
                    res = node.api_request("/api/cluster/management/conf/")
                    logger.debug(res)

            else:
                intf = Interface.objects.get(inet_addresses__in=[obj_inst])
                node = Node.objects.get(interfaces=intf)

                # First we shut down the listener on the corresponding node
                logger.info("Shutdown device {} on node {}".format(
                    intf.device, node.name))
                res = node.api_request(
                    "/api/network/listener/" + str(object_id) + "/down/")
                logger.debug(res)

                # Then delete Listener (bootstrap is true because rc_conf
                # refresh is done by hand)
                obj_inst.delete(bootstrap=True)

                # Then refresh rc_conf
                logger.info("Refresh rc_conf on node {}".format(node.name))
                res = node.api_request("/api/cluster/management/conf/")
                logger.debug(res)

        return HttpResponseRedirect(self.redirect_url)


class DeleteLoadBalancer(DeleteView):
    """Class dedicated to delete view of LoadBalancer object
    """
    menu_name = _("Load Balancer -> Delete")
    obj = Loadbalancer
    redirect_url = "/network/loadbalancer/"
    delete_url = "/network/loadbalancer/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            for backend in obj_inst.backends:
                try:
                    LoadbalancerBackend.objects.with_id(
                        ObjectId(backend.id)).delete()
                except Exception:
                    pass

            obj_inst.delete()
            return HttpResponseRedirect(self.redirect_url)


class DeleteAuth(DeleteView):
    """Class dedicated to delete view of Listener object

    """
    menu_name = _("Repository -> Delete")

    def get(self, request, object_id, obj_type,
            redirect_url, delete_url, **kwargs):
        self.obj = obj_type
        self.redirect_url = redirect_url
        self.delete_url = delete_url
        return super(DeleteAuth, self).get(request, object_id)

    def post(self, request, object_id, obj_type,
             redirect_url, delete_url, **kwargs):
        self.obj = obj_type
        self.redirect_url = redirect_url
        self.delete_url = delete_url
        confirm = request.POST.get('confirm')
        obj_inst = obj_type.objects.with_id(ObjectId(object_id))
        if not obj_inst:
            return HttpResponseForbidden("Injection detected.")
        # Users can't delete Internal Repository
        if confirm == 'yes' and not obj_inst.is_internal:
            obj_inst.delete()
        else:
            pass
        return HttpResponseRedirect(redirect_url)


class DeleteDataset(DeleteView):
    """Class dedicated to delete view of Dataset object

    """
    menu_name = _("Dataset Settings -> Delete")
    obj = Dataset
    redirect_url = "/datasets/"
    delete_url = "/dataset/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.only('id').with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            SVM.objects(dataset_used=obj_inst).only('id').delete()
            obj_inst.delete()
            return HttpResponseRedirect(self.redirect_url)


class DeleteImage(DeleteView):
    """
    Class dedicated to delete view of TemplateImage object
    """

    menu_name = _("Image -> Delete")
    obj = TemplateImage
    redirect_url = "/template/"
    delete_url = "/template/image/delete/"

    def post(self, request, object_id):
        confirm = request.POST.get('confirm')
        if confirm == 'yes':
            obj_inst = self.obj.objects.with_id(ObjectId(object_id))
            if not obj_inst:
                return HttpResponseForbidden("Injection detected.")
            obj_inst.content.delete()
            obj_inst.delete()
            return HttpResponseRedirect(self.redirect_url)
