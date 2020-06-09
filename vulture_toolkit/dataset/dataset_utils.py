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
__author__ = "Hubert Loiseau, Thomas Carayol, Olivier de Régis"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = ''

import json
from multiprocessing import Process

import matplotlib
import numpy as np
from bson.objectid import ObjectId
from sklearn import svm

from gui.models.dataset_settings import Dataset, SVM
from gui.models.modlog_settings import Logs
from vulture_toolkit.log.elasticsearch_client import ElasticSearchClient
from vulture_toolkit.log.mongodb_client import MongoDBClient

matplotlib.use('Agg')
import Levenshtein as leven

import time, datetime

import logging

logger = logging.getLogger('debug')


class Dataset_utils:
    def __init__(self, object_id):
        self.dataset = Dataset.objects.with_id(ObjectId(object_id))

    def build_dataset(self, date):
        self.application = self.dataset.application
        self.repo = self.application.log_custom.repository

        self.params = {
            'start'       : None,
            'length'      : None,
            'sorting'     : None,
            'type_sorting': None,
            'dataset'     : True,
            'type_logs'   : self.dataset.type_logs,
            'filter'      : {
                'rules'    : json.loads(self.dataset.search),
                'startDate': date['startDate'],
                'endDate'  : date['endDate'],
                'app'      : {
                    'name'        : self.application.name,
                    'public_dir'  : self.application.public_dir,
                    'public_name' : self.application.public_name,
                    'public_alias': self.application.public_alias
                }
            }
        }

        if self.repo.type_uri == 'elasticsearch':
            logger.info("Building dataset from ElasticSearch")
            p = Process(target=self._fetch_data_from_elasticsearch)
            p.start()
        elif self.repo.type_uri == 'mongodb':
            logger.info("Building dataset from MongoDB")
            p = Process(target=self._fetch_data_from_mongo)
            p.start()

    def _full_object(self, log, data):
        for key, value in data.items():
            try:
                try:
                    log[key] = json.loads(value)
                except:
                    log[key] = value
            except:
                pass

        return log

    def _fetch_data_from_elasticsearch(self):
        els = ElasticSearchClient(self.repo)
        result = els.search(self.params)
        self.dataset.nb_logs = 0

        for row in result['data']:
            logs = Logs()
            logs = self._full_object(logs, row)
            self.dataset.logs.append(logs)
            self.dataset.nb_logs += 1

        try:
            self.dataset.built = True
            logger.info("Dataset build")
            self.dataset.save()
            logger.info("Dataset saved")
        except Exception as e:
            logger.error("Failed to build dataset : ")
            logger.exception(e)
            self.dataset.built = False
            self.dataset.logs = []
            self.dataset.nb_logs = 0
            self.dataset.error = "Can't built dataset, too many logs"
            self.dataset.save()

    def _fetch_data_from_mongo(self):
        mongo = MongoDBClient(self.repo)
        result = mongo.search(self.params)
        self.dataset.nb_logs = 0

        for row in result['data']:
            logs = Logs()
            logs = self._full_object(logs, row)
            logs.type_logs = self.params['type_logs']
            self.dataset.logs.append(logs)
            self.dataset.nb_logs += 1

        try:
            self.dataset.built = True
            logger.info("Dataset build")
            self.dataset.save()
            logger.info("Dataset saved")
        except Exception as e:
            logger.error("Failed to build dataset : ")
            logger.exception(e)
            self.dataset.built = False
            self.dataset.logs = []
            self.dataset.nb_logs = 0
            self.dataset.error = "Can't built dataset, too many logs"
            self.dataset.save()

    def build_svm(self, gamma):
        self.dataset.svm_built = False
        self.dataset.save()

        try:
            self._build_httpcode_bytes_received(gamma=gamma['HTTP_code_bytes_received'])
        except Exception as e:
            logger.debug(e)

        try:
            self._build_httpcode_bytes_sent(gamma=gamma['HTTP_code_bytes_sent'])
        except Exception as e:
            logger.debug(e)

        try:
            self._build_leven(gamma=gamma['Levenstein'], number=True)
        except Exception as e:
            logger.debug(e)

        try:
            self._build_leven(gamma=gamma['Levenstein'], number=False)
        except Exception as e:
            logger.debug(e)

        try:
            self._build_request(gamma=gamma['Req_per_min_per_user'], choice="user")
        except Exception as e:
            logger.debug(e)

        try:
            self._build_request(gamma=gamma['Req_per_min_per_IP'], choice="ip")
        except Exception as e:
            logger.debug(e)

        try:
            self._build_ratio_bytes_received(gamma=gamma['Ratio'])
        except Exception as e:
            logger.debug(e)

        self.dataset.svm_built = True
        self.dataset.save()

    def _build_leven(self, gamma=0.00001, nu=0.01, number=True):
        """
        method used to analyse proximity and occurency of words in requested URI
        store the SVM called ML in mongo for later use
        :param request:
        :param dataset_id: dataset_id that we want to analyse
        :return:
        """
        if (number):
            data = list()
            liste = list()
            liste_dist = list()
            for log in self.dataset.logs:
                i = (log.requested_uri)
                if i is not None:
                    keys = i.split("/")
                    for key in keys:
                        if key not in liste:
                            liste.append(key)
            self.dataset.uri = liste

        else:
            data = list()
            liste = list()
            liste_dist = list()
            for log in self.dataset.logs:
                if log.requested_uri is not None:
                    i = log.requested_uri
                    if i not in liste:
                        liste.append(i)
            self.dataset.uri2 = liste

        self.dataset.save()

        for key in liste:
            liste_temp = list()
            for key2 in liste:
                dist = leven.distance(key, key2)
                liste_temp.append(dist)
            average = sum(liste_temp) / len(liste_temp)
            liste_dist.append([average, len(key)])
        # cast liste_dist list as a np.array
        X_train = np.array(liste_dist)
        # fit the model
        clf = svm.OneClassSVM(nu=nu, kernel="rbf", gamma=gamma)
        if gamma is not None and nu is not None:
            clf.gamma = gamma
            clf.nu = nu
        clf.fit(X_train)
        # get every fields of clf SVM
        dict_attr = clf.__dict__
        # if no SVM is found in the next instruction, we use a blank one
        # find the matching between dataset and algo used to choose the right SVM to retrieve (if it exist)
        if number:
            try:
                ML = SVM.objects(dataset_used=self.dataset.id, algo_used="Levenstein")[0]
            except:
                ML = SVM()
            ML.algo_used = 'Levenstein'
            ML.dataset_used = self.dataset

        else:
            try:
                ML = SVM.objects(dataset_used=self.dataset.id, algo_used="Levenstein2")[0]
            except:
                ML = SVM()
            ML.algo_used = 'Levenstein2'
            ML.dataset_used = self.dataset

        # Cast each fields of ML to the right type
        for attribute in dict_attr.keys():
            if isinstance(dict_attr[attribute], np.ndarray):
                ML[attribute] = dict_attr[attribute].tolist()
            elif isinstance(dict_attr[attribute], str) or isinstance(dict_attr[attribute], int) \
                    or isinstance(dict_attr[attribute], float) or isinstance(dict_attr[attribute], bool):
                ML[attribute] = dict_attr[attribute]
            elif isinstance(dict_attr[attribute], tuple):
                ML[attribute] = list(dict_attr[attribute])
            else:
                pass
        # store parameters of grid and points to generate graph later
        ML.grid_xx = [0, 400, 50]
        ML.grid_yy = [0, 400, 50]
        ML.app_used = self.dataset.application
        ML.built = True
        ML.save()

    def _build_httpcode_bytes_received(self, gamma=0.0003, nu=0.01):
        """
        method used to analyse the quantity of data generated by HTTP code
        store the SVM called ML in mongo for later use
        :param request:
        :param dataset_id: dataset_id that we want to analyse
        :return:
        """
        data = list()
        for log in self.dataset.logs:
            if self.dataset.type_logs == 'security':
                data.append((int(log.response_code), log.bytes_received))

            elif self.dataset.type_logs == 'access':
                data.append((int(log.http_code), log.bytes_received))

        # cast data list as a np.array
        X_train = np.array(data)
        clf = svm.OneClassSVM(nu=nu, kernel="rbf", gamma=gamma)
        if gamma is not None and nu is not None:
            clf.gamma = gamma
            clf.nu = nu
        clf.fit(X_train)
        # get every field of SVM clf
        dict_attr = clf.__dict__
        ML = SVM()
        # retrieve SVM from dataset_id and algo_used (if nothing found, ML is a blank SVM)
        try:
            ML = SVM.objects(dataset_used=self.dataset.id, algo_used="HTTPcode_bytes_received")[0]
        except:
            ML = SVM()

        ML.algo_used = 'HTTPcode_bytes_received'
        ML.dataset_used = self.dataset
        # Cast each fields of ML to the right type
        for attribute in dict_attr.keys():
            if isinstance(dict_attr[attribute], np.ndarray):
                ML[attribute] = dict_attr[attribute].tolist()
            elif isinstance(dict_attr[attribute], str) or isinstance(dict_attr[attribute], int) \
                    or isinstance(dict_attr[attribute], float) or isinstance(dict_attr[attribute], bool):
                ML[attribute] = dict_attr[attribute]
            elif isinstance(dict_attr[attribute], tuple):
                ML[attribute] = list(dict_attr[attribute])
            else:
                pass

        # store parameters of grid and points to generate graph later
        ML.grid_xx = [0, 1000, 500]
        ML.grid_yy = [0, 2000, 500]
        ML.app_used = self.dataset.application
        ML.built = True
        ML.save()

    def _build_request(self, gamma=0.0003, nu=0.01, choice=""):
        """
        """
        data = {}
        liste_size = list()

        repo = self.dataset.application.log_custom.repository
 
        for log in self.dataset.logs:
            if repo.type_uri == 'elasticsearch':
                # Format time = 2016-11-15T17:26:07+01:00
                date = datetime.datetime.strptime("1970:01:01 " + str(log.time).split('T')[1].split('+')[0], "%Y:%m:%d %H:%M:%S")
            elif repo.type_uri == 'mongodb':
                date = datetime.datetime.strptime("1970:01:01 " + str(log.time).split(' ')[1], "%Y:%m:%d %H:%M:%S")
            date = time.mktime(date.timetuple())
            if choice == "ip":
                try:
                    data[date][log.src_ip] += 1
                except KeyError:
                    data[date] = {log.src_ip: 1}
            elif choice == "user":
                try:
                    data[date][log.user] += 1
                except KeyError:
                    data[date] = {log.user: 1}
    
        for timestamp, value in data.items():
            liste_size.append([float(timestamp) / 1000, value.values()[0]])

        X_train = np.array(liste_size)
        # fit the model
        clf = svm.OneClassSVM(nu=nu, kernel="rbf", gamma=gamma)
        clf.fit(X_train)
        # get every fields of clf SVM
        dict_attr = clf.__dict__
        # find the matching between dataset and algo used to choose the right SVM to retrieve (if it exist)
        # if no SVM is found in the next instruction, we use a blank one
        if choice == "ip":
            try:
                ML = SVM.objects(dataset_used=self.dataset.id, algo_used="Req_per_min_per_ip")[0]
            except:
                ML = SVM()
            ML.algo_used = 'Req_per_min_per_ip'
            ML.dataset_used = self.dataset
        elif choice == "user":
            try:
                ML = SVM.objects(dataset_used=self.dataset.id, algo_used="Req_per_min_per_user")[0]
            except:
                ML = SVM()
            ML.algo_used = 'Req_per_min_per_user'
            ML.dataset_used = self.dataset
        # Cast each fields of ML to the right type
        for attribute in dict_attr.keys():
            if isinstance(dict_attr[attribute], np.ndarray):
                ML[attribute] = dict_attr[attribute].tolist()
            elif isinstance(dict_attr[attribute], str) or isinstance(dict_attr[attribute], int) \
                    or isinstance(dict_attr[attribute], float) or isinstance(dict_attr[attribute], bool):
                ML[attribute] = dict_attr[attribute]
            elif isinstance(dict_attr[attribute], tuple):
                ML[attribute] = list(dict_attr[attribute])
            else:
                pass
        # store parameters of grid and points to generate graph later
        ML.grid_xx = [0, 100, 50]
        ML.grid_yy = [0, 100, 50]
        ML.app_used = self.dataset.application
        ML.built = True
        ML.save()

    def _build_ratio_bytes_received(self, gamma=0.0003, nu=0.01):
        """
        method used to analyse the quantity of data generated by HTTP code
        store the SVM called ML in mongo for later use
        :param request:
        :param dataset_id: dataset_id that we want to analyse
        :return:
        """
        data = list()
        for log in self.dataset.logs:
            if self.dataset.type_logs == 'security':
                data.append((int(log.response_code), float(int(log.bytes_sent))/float(int(log.bytes_received))))
            elif self.dataset.type_logs == 'access':
                data.append((int(log.http_code), float(int(log.bytes_sent))/float(int(log.bytes_received))))

        # cast data list as a np.array
        X_train = np.array(data)
        clf = svm.OneClassSVM(nu=nu, kernel="rbf", gamma=gamma)
        if gamma is not None and nu is not None:
            clf.gamma = gamma
            clf.nu = nu
        clf.fit(X_train)
        # get every field of SVM clf
        dict_attr = clf.__dict__
        ML = SVM()
        # retrieve SVM from dataset_id and algo_used (if nothing found, ML is a blank SVM)
        try:
            ML = SVM.objects(dataset_used=self.dataset.id, algo_used="Ratio")[0]
        except:
            ML = SVM()

        ML.algo_used = 'Ratio'
        ML.dataset_used = self.dataset
        # Cast each fields of ML to the right type
        for attribute in dict_attr.keys():
            if isinstance(dict_attr[attribute], np.ndarray):
                ML[attribute] = dict_attr[attribute].tolist()
            elif isinstance(dict_attr[attribute], str) or isinstance(dict_attr[attribute], int) \
                    or isinstance(dict_attr[attribute], float) or isinstance(dict_attr[attribute], bool):
                ML[attribute] = dict_attr[attribute]
            elif isinstance(dict_attr[attribute], tuple):
                ML[attribute] = list(dict_attr[attribute])
            else:
                pass

        # store parameters of grid and points to generate graph later
        ML.grid_xx = [0, 2000, 500]
        ML.grid_yy = [0, 2000, 500]
        ML.app_used = self.dataset.application
        ML.built = True
        ML.save()

    def _build_httpcode_bytes_sent(self, gamma=0.0003, nu=0.01):
        """
        method used to analyse the quantity of data generated by HTTP code
        store the SVM called ML in mongo for later use
        :param request:
        :param dataset_id: dataset_id that we want to analyse
        :return:
        """
        data = list()
        for log in self.dataset.logs:
            if self.dataset.type_logs == 'security':
                data.append((int(log.response_code), log.bytes_sent))

            elif self.dataset.type_logs == 'access':
                data.append((int(log.http_code), log.bytes_sent))

        # cast data list as a np.array
        X_train = np.array(data)
        clf = svm.OneClassSVM(nu=nu, kernel="rbf", gamma=gamma)
        if gamma is not None and nu is not None:
            clf.gamma = gamma
            clf.nu = nu
        clf.fit(X_train)
        # get every field of SVM clf
        dict_attr = clf.__dict__
        ML = SVM()
        # retrieve SVM from dataset_id and algo_used (if nothing found, ML is a blank SVM)
        try:
            ML = SVM.objects(dataset_used=self.dataset.id, algo_used="HTTPcode_bytes_sent")[0]
        except:
            ML = SVM()

        ML.algo_used = 'HTTPcode_bytes_sent'
        ML.dataset_used = self.dataset
        # Cast each fields of ML to the right type
        for attribute in dict_attr.keys():
            if isinstance(dict_attr[attribute], np.ndarray):
                ML[attribute] = dict_attr[attribute].tolist()
            elif isinstance(dict_attr[attribute], str) or isinstance(dict_attr[attribute], int) \
                    or isinstance(dict_attr[attribute], float) or isinstance(dict_attr[attribute], bool):
                ML[attribute] = dict_attr[attribute]
            elif isinstance(dict_attr[attribute], tuple):
                ML[attribute] = list(dict_attr[attribute])
            else:
                pass
        # store parameters of grid and points to generate graph later
        ML.grid_xx = [0, 1000, 500]
        ML.grid_yy = [0, 2000, 500]
        ML.app_used = self.dataset.application
        ML.built = True
        ML.save()
