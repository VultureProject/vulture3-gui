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
__author__ = "Olivier de Régis, Thomas Carayol, Hubert Loiseau"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views dedicated to dataset configuration'

from multiprocessing import Process

from django.conf import settings

import matplotlib
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from numpy import int32, float64
from sklearn import svm

from gui.decorators import group_required
from gui.models.application_settings import Application
from gui.models.dataset_settings import Dataset, SVM
from gui.models.modsec_settings import ModSecRulesSet, ModSecRules
from gui.models.repository_settings import MongoDBRepository
from vulture_toolkit.dataset.dataset_utils import Dataset_utils
from vulture_toolkit.system.replica_set_client import ReplicaSetClient

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import Levenshtein as leven

import logging.config

import time
import hashlib
import json

from vulture_toolkit.log.mongodb_client import MongoDBClient
from vulture_toolkit.log.elasticsearch_client import ElasticSearchClient

from datetime import datetime, timedelta

from bson.objectid import ObjectId
from copy import deepcopy

logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('debug')


def get_collection(collection_name):
    """ Connect to MongoDB with MongoClient on internal database
         & return a pymongo.collection.Collection instance
    :param   collection_name  The collection name to connect to
    :return  A pymongo.collection.Collection object 
             or raise pymongo.errors.InvalidName if invalid name
    """
    repo = MongoDBRepository.objects.get(repo_name='Vulture Internal Database')
    client = MongoDBClient(repo)
    con = client._get_connection()
    db_logs = con.logs
    return db_logs[collection_name]


def drop_collection(collection_name):
    """ Connect to internal Database with MongoReplicasetClient and delete asked collection 
    :param   collection_name    The name of the collection to drop
    :return  Nothing
    """
    return ReplicaSetClient().get_database("logs").drop_collection(collection_name)


def update_collection(collection_name, query_filter, query_update):
    """ Modify objects into a collection
    :param   collection_name    The name of the collection to update
    :param   query_filter    The filter of objects to update
    :param   query_update    The update filter to apply on objects
    :return  The number of objects modified
    """
    db = ReplicaSetClient().get_database("logs")
    return db[collection_name].update_many(query_filter, query_update).modified_count


def remove_in_collection(collection_name, query_remove):
    """ Modify objects into a collection
    :param   collection_name    The name of the collection to update
    :param   query_remove    The filter of objects to delete
    :return  The number of objects deleted
    """
    db = ReplicaSetClient().get_database("logs")
    return db[collection_name].delete_many(query_remove).deleted_count


@group_required('administrator', 'application_manager', 'security_manager')
def svm_view(request, object_id):
    dataset = Dataset.objects(
        id=ObjectId(object_id)).only('name', 'id').first()
    return render_to_response('svm.html',
                              {'dataset': dataset},
                              context_instance=RequestContext(request))


@group_required('administrator', 'application_manager', 'security_manager')
def datasets(request):
    datasets = Dataset.objects.all().only(
        'id', 'name', 'app', 'nb_logs', 'built', 'error', 'svm_built')
    repo = MongoDBRepository.objects.get(repo_name='Vulture Internal Database')
    client = MongoDBClient(repo)
    con = client._get_connection()
    db_logs = con.logs
    cols = db_logs.collection_names()
    datasets_learning = []

    for col in cols:
        if not col.startswith('learning_'):
            continue

        try:
            app = Application.objects.only('name').with_id(ObjectId(col[9:]))
            uris = get_dataset_learning("learning_" + str(app.id), length=True)
            dataset = {"name": col, "phony": app.name +
                       " Defender Whitelist", "size": uris}
            datasets_learning.append(dataset)
        except Exception:
            continue

    return render_to_response('datasets.html',
                              {'datasets': datasets,
                               'datasets_learning': datasets_learning},
                              context_instance=RequestContext(request))


@group_required('administrator', 'application_manager', 'security_manager')
def dataset_edit(request, object_id=None):
    datasets = object_id
    return render_to_response('dataset_edit.html',
                              {'datasets': datasets},
                              context_instance=RequestContext(request))


@group_required('administrator', 'application_manager', 'security_manager')
def learning_edit(request, collection_name):
    return render_to_response('dataset_learning_edit.html',
                              {'collection_name': collection_name},
                              context_instance=RequestContext(request))


@group_required('administrator', 'application_manager', 'security_manager')
def generate_wl(request, collection_name):
    col = get_collection(collection_name)
    data = list(col.find({"whitelisted": {"$eq": "false"}}))
    app = Application.objects.only('name').with_id(
        ObjectId(collection_name[9:]))

    rs_name = "Learning " + app.name + " WL"
    try:
        ruleset = ModSecRulesSet.objects.get(name=rs_name)
    except ModSecRulesSet.DoesNotExist:
        ruleset = ModSecRulesSet(name=rs_name, type_rule='vulture')
        ruleset.save()

    rule_name = "Learning " + app.name + " rule"
    rule = ModSecRules.objects.filter(name=rule_name, rs=ruleset).first()
    if not rule:
        rule = ModSecRules(name=rule_name, rs=ruleset,
                           is_enabled=True, date_rule=datetime.now())

    wls = set()
    if rule.rule_content:
        wls = set(rule.rule_content.splitlines())
    for record in data:
        url = record['uri']

        entries = []
        for ridx in range(10):
            if not 'id' + str(ridx) + '_0' in record:
                break

            entry = {'ids': []}
            for ridx2 in range(10):
                if not 'id' + str(ridx) + '_' + str(ridx2) in record:
                    break
                entry['ids'].append(
                    str(record['id' + str(ridx) + '_' + str(ridx2)]))
            entry['zone'] = record['zone' + str(ridx)]
            entry['effective_zone'] = entry['zone']
            entry['target_name'] = False
            if entry['zone'].endswith("|NAME"):
                entry['target_name'] = True
                entry['effective_zone'] = entry['zone'][0:-5]
            entry['var_name'] = record.get('var_name' + str(ridx))
            entry['content'] = record.get('content' + str(ridx))
            entries.append(entry)

        for ent in entries:
            if ent['effective_zone'] in ["ARGS", "BODY", "HEADERS"]:
                r = 'BasicRule wl:' + \
                    ','.join(ent['ids']) + ' "mz:$URL:' + url + '|$' + \
                    ent['effective_zone'] + '_VAR:' + ent['var_name'] + \
                    ("|NAME" if ent["target_name"] else '') + '";'
                if r not in wls:
                    wls.add(r)
            else:
                r = 'BasicRule wl:' + \
                    ','.join(ent['ids']) + ' "mz:$URL:' + url + '|URL";'
                if r not in wls:
                    wls.add(r)

    rule.rule_content = "\n".join(wls) + "\n"
    rule.save()

    ruleset.conf = ruleset.get_conf()
    ruleset.save()

    nb_updated = update_collection(collection_name,
                      {"whitelisted": "false"},
                      {"$set": {"whitelisted": "true"}})
    logger.info("DATASET::Generate_WL: {} document(s) updated".format(nb_updated))

    return JsonResponse({'status': True})


@group_required('administrator', 'application_manager', 'security_manager')
def delete_learning(request, collection_name):
    try:
        drop_collection(collection_name)
    except Exception as e:
        logger.error("Failed to drop collection '{}'".format(collection_name))
        logger.exception(e)
        return JsonResponse({'status':False, 'message': str(e)})
    return JsonResponse({'status': True})


@group_required('administrator', 'application_manager', 'security_manager')
def add_wl(request, collection_name):
    try:
        wls = json.loads(request.POST['wls'])
    except:
        logger.error("DATASET::Add_WL: wls POST variable is not JSON type")
        return JsonResponse({'status': False, 'message': "Whitelist format invalid."})
    try:
        log_id = request.POST['id']
    except:
        logger.error("DATASET::Add_WL: Log_id variable missing.")
        return JsonResponse({'status': False, 'message': "Log_id missing."})
    try:
        app = Application.objects.only('name').with_id(ObjectId(collection_name[9:]))
    except:
        logger.error("DATASET::Add_WL: Application having id {} not found.".format(collection_name[9:]))
        return JsonResponse({'status': False,
                             'message': "Application {} not found.".format(collection_name[9:])})

    rs_name = "Learning " + app.name + " WL"
    try:
        ruleset = ModSecRulesSet.objects.get(name=rs_name)
    except ModSecRulesSet.DoesNotExist:
        logger.info("DATASET::Add_WL: ModSecRulesSet '{}' not found. Creating-it.".format(rs_name))
        ruleset = ModSecRulesSet(name=rs_name, type_rule='vulture')
        ruleset.save()

    rule_name = "Learning " + app.name + " rule"
    rule = ModSecRules.objects.filter(name=rule_name, rs=ruleset).first()
    if not rule:
        rule = ModSecRules(name=rule_name, rs=ruleset,
                           is_enabled=True, date_rule=datetime.now())

    if not rule.rule_content:
        rule.rule_content = ""

    content_modified = False
    for wl in wls:
        if wl not in rule.rule_content:
            rule.rule_content += wl + "\n"
            content_modified = True
    if content_modified:
        rule.save()
        logger.info("ModSecRule {} updated.".format(rule.name))
        ruleset.conf = ruleset.get_conf()
        ruleset.save()
        logger.info("ModSecRulesSet {} updated.".format(ruleset.name))

    try:
        nb_updated = update_collection(collection_name,
                                       {"_id": ObjectId(log_id)},
                                       {"$set": {"whitelisted": "true"}})
        logger.info("DATASET::Add_WL: Entries updated : {}".format(nb_updated))
    except Exception as e:
        logger.error("DATASET::Add_WL: Fail to update entry '{}' in collection '{}'.".format(log_id, collection_name))
        logger.exception(e)
        return JsonResponse({'status': False,
                             'message': "Failed to update log '{}'".format(log_id)})

    return JsonResponse({'status': True})


@group_required('administrator', 'application_manager', 'security_manager')
def dataset_add(request):
    type_logs = request.POST['type_select']
    search = request.POST['search']
    dataset_name = request.POST['dataset_name']
    app_id = request.POST['app_id']
    date = json.loads(request.POST['date'])
    app = Application.objects.with_id(ObjectId(app_id))

    dataset = Dataset(name=dataset_name, search=search,
                      type_logs=type_logs, application=app, built=False)
    dataset.save()
    logger.info("Dataset successfully saved. Building-it ...")
    Dataset_utils(dataset.id).build_dataset(date)
    return JsonResponse({'status': True})


@group_required('administrator', 'application_manager', 'security_manager')
def dataset_status(request):
    dataset_id = request.POST['dataset_id']
    data_type = request.POST['type']

    try:
        dataset = Dataset.objects.only(data_type).with_id(ObjectId(dataset_id))
    except Exception:
        return JsonResponse({'status': False})

    return JsonResponse({'status': getattr(dataset, request.POST['type'])})


@group_required('administrator', 'application_manager', 'security_manager')
def dataset_list(request):
    app_id = request.POST['app_id']
    datasets = Dataset.objects.filter(application=ObjectId(app_id))
    data = []

    for row in datasets:
        data.append({
            'id': str(row.id),
            'name': row.name,
        })

    return JsonResponse({'status': True, 'datasets': json.dumps(data)})


def get_dataset_learning(collection_name, length=False):
    col = get_collection(collection_name)

    if not length:
        uris = []
        for uri in list(col.find({}).sort([('_id', -1)])):
            uri['_id'] = str(uri['_id'])
            uris.append(uri)
    else:
        uris = col.find({}).sort([('_id', -1)]).count()

    return uris


@group_required('administrator', 'application_manager', 'security_manager')
def dataset_get_learning(request):
    dataset_collection_name = request.POST['dataset_collection_name']
    uris = get_dataset_learning(dataset_collection_name)

    return JsonResponse({
        "iTotalRecords": len(uris),
        "iTotalDisplayRecords": len(uris),
        "aaData": uris
    })


@group_required('administrator', 'application_manager', 'security_manager')
def dataset_get(request):
    dataset_id = request.POST['dataset_id']
    columns = json.loads(request.POST['columns'])

    try:
        dataset = Dataset.objects.with_id(ObjectId(dataset_id))
        start = int(request.POST['iDisplayStart'])
        length = int(request.POST['iDisplayLength']) + start
    except Exception:
        return JsonResponse({
            'status': False
        })

    data = []
    for log in dataset.logs[start:length]:
        temp = {
            'check': "<input type='checkbox' class='select_logs' data-id='{}'/>".format(log._id)}
        for col in columns:
            temp[col] = getattr(log, col)
        data.append(temp)
    return JsonResponse({
        "iTotalRecords": len(dataset.logs),
        "iTotalDisplayRecords": len(dataset.logs),
        "aaData": data
    })


@group_required('administrator', 'application_manager', 'security_manager')
def remove_logs(request):
    dataset_id = request.POST['dataset_id']
    try:
        dataset = Dataset.objects.with_id(ObjectId(dataset_id))
    except Exception:
        return JsonResponse({'status': False})

    to_remove = json.loads(request.POST['to_remove'])
    log_list = []

    for log in dataset.logs:
        if str(log._id) not in to_remove:
            log_list.append(log)

    dataset.logs = log_list
    dataset.save()
    return JsonResponse({'status': True})


@group_required('administrator', 'application_manager', 'security_manager')
def remove_logs_learning(request):
    try:
        dataset_collection_name = request.POST['dataset_collection_name']
        to_remove = json.loads(request.POST['to_remove'])
        nb_removed = remove_in_collection(dataset_collection_name, {"_id": {"$in": [ObjectId(x) for x in to_remove]}})
        logger.info("DATASET::Remove_logs_learning: Number of logs deleted : {}".format(nb_removed))
        return JsonResponse({'status': True})
    except Exception as e:
        logger.exception("DATASET::Remove_logs_learning: ")
        return JsonResponse({'status': False, 'message': str(e)})


@group_required('administrator', 'application_manager', 'security_manager')
def dataset_build(request, object_id):
    try:
        gamma = {
            'HTTP_code_bytes_received': float(request.POST['HTTP_code_bytes_received']),
            'HTTP_code_bytes_sent': float(request.POST['HTTP_code_bytes_sent']),
            'Levenstein': float(request.POST['Levenstein']),
            'Req_per_min_per_IP': float(request.POST['Req_per_min_per_IP']),
            'Req_per_min_per_user': float(request.POST['Req_per_min_per_user']),
            'Ratio': float(request.POST['Ratio']),
        }
    except Exception:
        return JsonResponse({'status': False})

    d = Dataset_utils(object_id)
    p = Process(target=d.build_svm, args=(gamma,))
    p.start()
    return JsonResponse({'status': True})


def retrieve_SVM(dataset_id, algo_used):
    """
    method used to instantiate SVM stored in mongoDB from dataset_id
    :param dataset_id: dataset id that we want to find which SVM used
    :param algo_used: if there's different SVM with dif# andferent algo used, we use this to differentiate them
    :return: SVM found in the database instantiated and grid associated with this SVM, xx and yy grid parameters
        and points of the graph
    """

    try:
        mysvm = SVM.objects(dataset_used=dataset_id, algo_used=algo_used)[0]
    except Exception:
        return None

    ML = svm.OneClassSVM(
        gamma=mysvm.gamma, coef0=mysvm.coef0, max_iter=mysvm.max_iter)
    # retrieve parameters of SVM in mongoDB to put them into the newly
    # instantiated SVM
    for attribute in mysvm._fields.keys():
        if attribute in ('grid_xx', 'dataset_used', 'grid_yy',
                         'gamma', 'coef0', 'max_iter', 'algo_used'):
            continue
        elif attribute == "shape_fit_":
            ML.__setattr__(attribute, tuple(mysvm[attribute]))
        elif isinstance(mysvm[attribute], list):
            if attribute == "n_support_" or attribute == "support_":
                ML.__setattr__(attribute, np.array(
                    mysvm[attribute], dtype=int32))
            else:
                ML.__setattr__(attribute, np.array(
                    mysvm[attribute], dtype=float64))
        else:
            ML.__setattr__(attribute, mysvm[attribute])
    ML._impl = 'one_class'
    xx = mysvm.grid_xx
    yy = mysvm.grid_yy
    return ML, xx, yy


@csrf_exempt
@group_required('administrator', 'application_manager', 'security_manager')
def print_graph(request):
    """
    :param request: contains dataset_id and algo_used to instantiate SVM
    :return: points and curve of learning frontier from dataset to show on graph
    """
    algo_used = request.POST['algo_used']

    try:
        svm, grid_x, grid_y = retrieve_SVM(
            ObjectId(request.POST['dataset_id']), algo_used)
    except Exception:
        return JsonResponse({'status': False})

    xx, yy = np.meshgrid(np.linspace(grid_x[0], grid_x[1], grid_x[
                         2]), np.linspace(grid_y[0], grid_y[1], grid_y[2]))
    Z = svm.decision_function(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    a = plt.contour(xx, yy, Z, levels=[0])
    t = a.collections[0].get_paths()
    contour = list()
    for i in t:
        contour.append(i.vertices.tolist())

    return JsonResponse({"contour": contour})


@csrf_exempt
def graph_realtime(request):
    """
    :param request:
    :return:
    """
    dataset_id = request.POST['dataset_id']
    dataset = Dataset.objects.only(
        'application', 'uri', 'uri2').with_id(ObjectId(dataset_id))
    algo_used = request.POST['algo_used']
    app = dataset.application
    repo = app.log_custom.repository

    if isinstance(repo, MongoDBRepository):
        client = MongoDBClient(repo)
    else:
        client = ElasticSearchClient(repo)

    now = datetime.now()
    if "Req_per_min_per" in algo_used:
        before = now - timedelta(seconds=60)
    else:
        before = now - timedelta(seconds=5)

    # columns = {
    #     'Levenstein': "_id,requested_uri,src_ip",
    #     'Levenstein2': "_id,requested_uri,src_ip",
    #     'HTTPcode_bytes_received': "_id,http_code,bytes_received,src_ip,requested_uri",
    #     "HTTPcode_bytes_sent": "_id,http_code,bytes_sent,src_ip,requested_uri",
    #     "Req_per_min_per_ip": "_id,src_ip,time",
    #     "Req_per_pin_per_user": "_id,user,time,src_ip",
    #     "Ratio": "_id,http_code,bytes_received,bytes_sent,requested_uri"
    # }

    params = {
        'dataset': True,
        'sorting': "time",
        'type_sorting': "desc",
        'type_logs': "access",
        'columns': algo_used,
        'start': 0,
        'length': 20,
        'filter': {
            'rules': {},
            'startDate': before.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'endDate': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'app': {
                'public_name': app.public_name,
                'public_dir': app.public_dir,
                'name': app.name,
                'public_alias': app.public_alias,
            }
        }
    }

    result = client.search(params, id_query=None)['data']
    liste_dist, AnomalyArray, data, info, liste_sympa = [], [], [], [], []

    if len(result):
        mysvm, temp1, temp2 = retrieve_SVM(ObjectId(dataset_id), algo_used)

        if algo_used == "Levenstein":
            uri = dataset.uri
            for i in result:
                for j in i['requested_uri'].split("/"):
                    if j != "" and j not in liste_sympa:
                        liste_sympa.append(j)
            for key in liste_sympa:
                liste_temp = list()
                for key2 in uri:
                    dist = leven.distance(str(key), str(key2))
                    liste_temp.append(dist)
                average = sum(liste_temp) / len(liste_temp)
                liste_dist.append([average, len(key)])
                info.append(key)
            data = liste_dist
            if len(liste_dist):
                AnomalyArray = mysvm.predict(np.array(data)).tolist()

        elif algo_used == "Levenstein2":
            uri = dataset.uri2
            for i in result:
                if i['requested_uri'] != "/" \
                        and i['requested_uri'] not in liste_sympa:
                    liste_sympa.append(i['requested_uri'])
            for key in liste_sympa:
                liste_temp = list()
                for key2 in uri:
                    dist = leven.distance(str(key), str(key2))
                    liste_temp.append(dist)
                average = sum(liste_temp) / len(liste_temp)
                liste_dist.append([average, len(key)])
                info.append(key)
            data = liste_dist
            if len(liste_dist):
                AnomalyArray = mysvm.predict(np.array(data)).tolist()

        elif algo_used == "HTTPcode_bytes_received":
            for i in result:
                info.append(i['src_ip'] + " " + i["requested_uri"])
                data.append([int(i["http_code"]), i["bytes_received"]])
            if len(data):
                AnomalyArray = mysvm.predict(np.array(data)).tolist()

        elif algo_used == "HTTPcode_bytes_sent":

            for i in result:
                info.append(i['src_ip'] + " " + i["requested_uri"])
                data.append([int(i["http_code"]), i["bytes_sent"]])
            if len(data):
                AnomalyArray = mysvm.predict(np.array(data)).tolist()

        elif algo_used == "Ratio":
            for i in result:
                data.append([int(i["http_code"]), int(
                    i["bytes_sent"]) / int(i["bytes_received"])])
                info.append(str(i["src_ip"]) + " " + str(i["requested_uri"]))
            if len(data):
                AnomalyArray = mysvm.predict(np.array(data)).tolist()

        elif algo_used == "Req_per_min_per_ip":
            dico = dict()
            for i in result:
                date = datetime.strptime(
                    "1970:01:01 " + str(i['time']).split(' ')[1],
                    "%Y:%m:%d %H:%M:%S"
                )

                date = time.mktime(date.timetuple())
                try:
                    dico[date][i['src_ip']] += 1
                except KeyError:
                    dico[date] = {i['src_ip']: 1}

            for timestamp, value in dico.items():
                data.append([float(timestamp) / 1000, value.values()[0]])
                info.append(value.keys()[0])

            if len(data):
                AnomalyArray = mysvm.predict(np.array(data)).tolist()

        elif algo_used == "Req_per_min_per_user":
            dico = dict()
            for i in result:
                date = datetime.strptime(
                    "1970:01:01 " + str(i['time']).split(' ')[1],
                    "%Y:%m:%d %H:%M:%S"
                )

                date = time.mktime(date.timetuple())
                try:
                    dico[date][i['user']] += 1
                except KeyError:
                    dico[date] = {i['user']: 1}
            for timestamp, value in dico.items():
                data.append([float(timestamp) / 1000, value.values()[0]])
                info.append(value.keys()[0])

            if len(data):
                AnomalyArray = mysvm.predict(np.array(data)).tolist()

        for key, sub_data in enumerate(data):
            try:
                data[key].append(info[key])
            except Exception:
                continue

    return JsonResponse({"data": data, "anomaly": AnomalyArray})
