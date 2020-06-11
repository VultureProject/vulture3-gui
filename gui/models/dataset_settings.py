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
__doc__ = 'Django models dedicated to dataset'

from mongoengine import (BooleanField, DynamicDocument, EmbeddedDocumentField, FloatField, IntField, ListField, PULL,
                         ReferenceField, StringField)
from django.conf import settings
from gui.models.application_settings import Application
from gui.models.modlog_settings import Logs
from vulture_toolkit.templates import tpl_utils
import os
import numpy as np
import binascii
import codecs
from bson import ObjectId


class Dataset(DynamicDocument):
    """ Dataset object
    name       : Name of the dataset
    search     : Search query use for fetch the logs
    type_logs  : Type of logs use
    application: Link to the application
    logs       : List of logs
    """
    name        = StringField(required=True)
    search      = StringField(required=True)
    type_logs   = StringField(required=True)
    application = ReferenceField(Application, required=True, reverse_delete_rule=PULL)
    logs        = ListField(EmbeddedDocumentField(Logs))
    nb_logs     = IntField()
    error       = StringField(default="")
    built       = BooleanField(default=False)
    svm_built   = BooleanField()
    uri         = ListField()
    uri2        = ListField()


class SVM(DynamicDocument):
    """ SVM object
    support_ : array-like, shape = [n_SV]
    Indices of support vectors. support_vectors_ : array-like, shape = [nSV, n_features]
    dual_coef_ : array, shape = [n_classes-1, n_SV]
    Coefficients of the support vectors in the decision function.
    coef_ : array, shape = [n_classes-1, n_features]
    Weights assigned to the features (coefficients in the primal problem). This is only available in the case of a linear kernel.
    coef_ is readonly property derived from dual_coef_ and support_vectors_
    intercept_ : array, shape = [n_classes-1]
    Constants in decision function.
    """
    ALGORITHMS = (
        ('Levenstein', 'Levenstein'),
        ('Levenstein2', 'Levenstein2'),
        ('HTTPcode_bytes_received', 'HTTPcode_bytes_received'),
        ('HTTPcode_bytes_sent', 'HTTPcode_bytes_sent'),
        ('Req_per_min_per_ip', 'Req_per_min_per_ip'),
        ('Map', 'Map'),
        ('Ratio', 'Ratio'),
        ('Req_per_min_per_user', 'Req_per_min_per_user')
    )
    algo_used = StringField(required=True, choices=ALGORITHMS)
    dataset_used = ReferenceField(Dataset, required=True)
    built = BooleanField(default=False)
    _impl = StringField()
    kernel = StringField()
    verbose =BooleanField()
    probability = BooleanField()
    support_ = ListField()
    dual_coef_ = ListField()
    shrinking = BooleanField()
    # class_weight = NoneType
    _gamma = FloatField()
    probA_  = ListField()
    _sparse = BooleanField()
    class_weight_ = ListField()
    # random_state = NoneType
    tol = FloatField()
    coef0 =FloatField()
    nu = FloatField()
    n_support_  = ListField()
    shape_fit_  = ListField()  #====> TUPLE /!\
    C = FloatField()
    support_vectors_ = ListField()
    _dual_coef_ = ListField()
    degree = IntField()
    epsilon = FloatField()
    max_iter = IntField()
    fit_status_ = IntField()
    _intercept_ = ListField()
    intercept_ = ListField()
    probB_ = ListField()
    cache_size = IntField()
    gamma = FloatField()
    grid_xx = ListField()
    grid_yy = ListField()


    def write_conf(self, config):
        path = self.conf_directory
        # Creating SVMs directory
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except Exception as e:
                print("Directory already exists: " + str(path))
                print(str(e))
        # Writing svm file
        filename = self.get_config_file()
        # Unlink file, just to be sure...
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                print("Unable to delete file: " + str(filename))
                print(e)
        # Creating rule file
        try:
            with codecs.open(filename, "w", encoding='utf8') as f:
                f.write(config)
        except Exception as e:
            print("Unable to write svm_conf '{}' - reason is: {}".format(self.id, str(e)))
            print(str(e))
            return False

        return True


    def getConf(self):
        parameters = dict()
        ret = dict()
        ret['error'] = ""
        try:
            parameters['nrclass'] = str( np.array(self.n_support_).shape[0] )
            parameters['SVdims'] = str(np.array(self.support_vectors_).shape[0])+" "+str(np.array(self.support_vectors_).shape[1])
            parameters['SV'] = little_endian(str(binascii.hexlify(np.array(self.support_vectors_).data)),16)
            try:
                parameters['supportdims'] = str(np.array(self.support_).shape[0])+" "+str(np.array(self.support_).shape[1])
            except:
                parameters['supportdims'] = str(np.array(self.support_).shape[0])+" 1"
            parameters['support'] = little_endian(str(binascii.hexlify(np.array(self.support_).data)),8)
            parameters['SVcoef'] = little_endian(str(binascii.hexlify(np.array(self.dual_coef_).data)),16)
            parameters['rho'] = little_endian(str(binascii.hexlify(np.array(self._intercept_).data)),16)
            parameters['nSV'] = little_endian(str(binascii.hexlify(np.array(self.n_support_).data)),8)
            parameters['SVcoefstrides'] = str(np.array(self._dual_coef_).strides[0])+" "+str(np.array(self._dual_coef_).strides[1])
            parameters['gamma'] = str("%.17f"%self.gamma)
        except Exception as e:
            ret['error'] = str(e)
        prefix = ""

        if self.algo_used == "Levenstein":
            svm = SVM.objects(id=ObjectId(self.id)).no_dereference().only('dataset_used').first()
            liste_uris = Dataset.objects(id=svm.dataset_used.id).only('uri').first().uri
            parameters['uris'] = "/".join(liste_uris)
            prefix = "svm2"
        elif self.algo_used == "Levenstein2":
            svm = SVM.objects(id=ObjectId(self.id)).no_dereference().only('dataset_used').first()
            liste_uris = Dataset.objects(id=svm.dataset_used.id).only('uri').first().uri
            parameters['uris'] = ";".join(liste_uris)
            prefix = "svm3"
        elif self.algo_used == "HTTPcode_bytes_received":
            prefix = "svm4"
        elif self.algo_used == "Ratio":
            prefix = "svm5"
        if not prefix:
            ret['error'] = ['<br/>SVM algorithm not recognized or not compatible']
        else:
            t = tpl_utils.get_template("vulture_"+prefix)[0]
            ret['config'] = t.render(conf=parameters)
        return ret


    @property
    def conf_directory(self):
        """ Directory where confs are stored

        :return:
        """
        return '{}svm/'.format(settings.CONF_DIR)


    def get_config_file(self):
        prefix = ""
        if self.algo_used == "Levenstein":
            prefix = "svm2"
        elif self.algo_used == "Levenstein2":
            prefix = "svm3"
        elif self.algo_used == "HTTPcode_bytes_received":
            prefix = "svm4"
        elif self.algo_used == "Ratio":
            prefix = "svm5"
        if not prefix:
            return ""
        else:
            return '{}{}_{}.conf'.format(self.conf_directory, str(self.dataset_used.id), prefix)


def little_endian(string, size):
    to_return = ""
    if size == 8:
        for i in range(0, len(string), 8):
            to_return += string[i+6:i+8]+string[i+4:i+6]+string[i+2:i+4]+string[i:i+2]
    if size == 16:
        for i in range(0, len(string), 16):
            to_return += string[i+14:i+16]+string[i+12:i+14]+string[i+10:i+12]+string[i+8:i+10]+string[i+6:i+8]+string[i+4:i+6]+string[i+2:i+4]+string[i:i+2]
    return to_return
