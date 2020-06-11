#!/home/vlt-gui/env/bin/python2.7
# coding:utf-8
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
__author__ = "Guillaume Catto, Kevin Guillemot"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = """Migration script to apply new config for indexes"""

# MONGO IMPORT REQUIRED
from sys import path as sys_path, exit as sys_exit
sys_path.append("/home/vlt-gui/vulture")
from os import environ
environ.setdefault("DJANGO_SETTINGS_MODULE", "vulture.settings")

# Django system imports
import django
django.setup()

# Django project imports
from gui.models.repository_settings import MongoDBRepository
from gui.models.system_settings import Cluster
from vulture_toolkit.log.mongodb_client import MongoDBClient, BulkWriteError

# Logger configuration imports
import logging
logger = logging.getLogger('cluster')



# Custom exceptions definition
class UpdateCrash(Exception):
    """ This exception is raised when something went wrong 
    during the migration process
    """
    def __init__(self, message):
        super(UpdateCrash, self).__init__(message)



def get_zone_index(key):
    """Return the index of a zone{index} key.

    Args:
        key (str): the key from which to get the index from.

    Returns:
        str: the index extracted from the zone key.
    """
    try:
        return key.split("zone", 1)[1]
    except Exception:
        raise Exception("Malformed zone key: " + key)


def get_var_name_index(key):
    """Return the index of a var_name{index} key.

    Args:
        key (str): the key from which to get the index from.

    Returns:
        str: the index extracted from the var_name key.
    """
    try:
        return key.split("var_name", 1)[1]
    except Exception:
        raise Exception("Malformed var_name key: " + key)


def get_rule_index(key):
    """Return the index of a id{index}_{id_number} key.

    Args:
        key (str): the key from which to get the index from.

    Returns:
        str: the index extracted from the id key.
    """
    try:
        start = 2
        end = key.index("_", start)

        return key[start:end]
    except Exception:
        raise Exception("Malformed id key: " + key)


def add_to_dict(index, hit, key, data_dict):
    """Add the key/value to the given dict (depending if it is an id, var_name
    or zone).

    Args:
        index (str): the index of the dict to add the key/value to.
        hit (dict): the hit to save in the new collection.
        key (str): the key of the hit to save in the dictionary.
        data_dict (dict): the id, var_name or zone dictionary.
    """
    try:
        data_dict[index].append(hit[key])
    except KeyError:
        data_dict[index] = [hit[key]]


def concatenate_results(zone_dict, rule_id_dict, var_name_dict, uri):
    """From the different dicts (id, var_name and zone) and the uri field,
    create a context_id and return it.

    Args:
        zone_dict (dict): the zone dictionary
        rule_id_dict (dict): the id dictionary
        var_name_dict (dict): the var_name dictionary
        uri (str): the value of the uri key in the hit

    Returns:
        str: the context_id created with the parameters.
    """
    # from the different dicts (id, var_name and zone) and the uri field,
    # create a context_id and return it
    context_id = ""

    try:
        zone_max = max(zone_dict, key=int)
    except:
        zone_max = -1
    try:
        rule_id_max = max(rule_id_dict, key=int)
    except:
        rule_id_max = -1
    try:
        var_name_max = max(var_name_dict, key=int)
    except:
        var_name_max = -1

    max_index = max(zone_max, rule_id_max, var_name_max)
    max_index = int(max_index)

    for index in range(0, max_index + 1):
        index_str = str(index)

        try:
            zone_str = "".join(
                [zone_str for zone_str in zone_dict[index_str]]
            )
        except KeyError:
            zone_str = ""
            pass

        try:
            rule_id_str = "".join(
                [str(rule_id_str) for rule_id_str in rule_id_dict[index_str]]
            )
        except KeyError:
            rule_id_str = ""
            pass

        try:
            var_name_str = "".join(
                [var_name_str for var_name_str in var_name_dict[index_str]]
            )
        except KeyError:
            var_name_str = ""
            pass

        context_id += zone_str + rule_id_str + var_name_str

    context_id += uri

    return context_id


def get_context_id(hit):
    """Assign the different key/value couples to the right dictionaries (id,
    var_name and zone) and create a context_id string with the uri field.

    Args:
        hit (dict): the hit to save in the new collection.

    Returns:
        str: the context_id created from the hit.
    """
    sorted_keys = sorted(hit)

    zone_dict = {}
    rule_id_dict = {}
    var_name_dict = {}
    uri = ""

    zone_pattern = "zone"
    rule_id_pattern = "id"
    var_name_pattern = "var_name"
    uri_pattern = "uri"

    for key in sorted_keys:
        if key.startswith(zone_pattern):
            add_to_dict(get_zone_index(key), hit, key, zone_dict)
        elif key.startswith(rule_id_pattern):
            add_to_dict(get_rule_index(key), hit, key, rule_id_dict)
        elif key.startswith(var_name_pattern):
            add_to_dict(get_var_name_index(key), hit, key, var_name_dict)
        elif key.startswith(uri_pattern):
            uri = hit[key]

    return concatenate_results(zone_dict, rule_id_dict, var_name_dict, uri)


def insert_hits(hits_to_insert, col):
    """Insert hits a given collection, using a bulk insert.

    Args:
        hits_to_insert (list): the list of hits to insert.
        col (Collection): the collection to insert the hits to.
    """
    try:
        col.insert_many(hits_to_insert, ordered=False)
    except BulkWriteError:
        pass  # we ignore errors with duplicates


def create_new_collections(db_logs):
    """Create the new collections as in new_learning_{id} for a learning_{id}
    collection.

    Args:
        db_logs (MongoDatabase): the logs MongoDB database.
    """
    cols = db_logs.collection_names()
    collection_len = 0
    collection_processed = 0

    for col_name in cols:
        if not col_name.startswith("learning_"):
            continue

        collection_len += 1
        # first, we get the current collection...
        col = db_logs[col_name]

        new_col = db_logs.create_collection("new_" + col_name)

        # which will be copied with a new key...
        new_col.create_index(
            "context_id",
            unique=True
        )

        # we will bulk insert all the hits for performance purposes
        hits_to_insert = []

        # but... we have to limit the bulk insert to avoid RAM issues
        max_length = 10000

        nb_hits_processed = 0
        # for each hit, we copy it with the new key created
        for hit in col.find():
            context_id = get_context_id(hit)

            hit["context_id"] = context_id
            hits_to_insert.append(hit)
            nb_hits_processed += 1

            # oops, too much to insert already: let's do it
            if len(hits_to_insert) >= max_length:
                insert_hits(hits_to_insert, new_col)
                hits_to_insert = []

        # maybe some results were not inserted
        if len(hits_to_insert) > 0:
            insert_hits(hits_to_insert, new_col)

        collection_processed += 1

        logger.info("Number of hits processed: {}, new number of hits: {}".format(nb_hits_processed, new_col.count()))
        logger.info("Collection {collection_name} successfully processed, ".format(collection_name=col_name))

    if collection_len != collection_processed:
        raise Exception("Some collections were unprocessed for some reason")

    logger.info("New collection(s) successfully created")


def delete_new_learning_collections(db_logs):
    """When something went wrong, we delete all the changes we've made in the
    MongoDB database.

    Args:
        db_logs (MongoDatabase): the logs MongoDB database.
    """
    new_cols = db_logs.collection_names()

    for new_col_name in new_cols:
        # that being said, we have to remove the new collections
        if new_col_name.startswith("new_learning_"):
            db_logs[new_col_name].drop()
            logger.info("New temporary collection {} dropped".format(new_col_name))


def transfer_new_collections(db_logs):
    """When we've successfully created all the collections. Now is the time to
    delete the old ones, and rename the new ones with the old name.

    Args:
        db_logs (MongoDatabase): the logs MongoDB database.
    """
    new_cols = db_logs.collection_names()
    prefix = "new_learning_"
    prefix_len = len(prefix)

    for new_col_name in new_cols:
        # we start from the new collection
        if not new_col_name.startswith(prefix):
            continue

        old_col_name = "learning_" + new_col_name[prefix_len:]

        # we delete the old collection, to rename the new one after
        db_logs[old_col_name].drop()
        logger.info("Collection {} successfully dropped".format(new_col_name))

        db_logs[new_col_name].rename(old_col_name)
        logger.info("Collection {} successfully renamed to {}".format(new_col_name, old_col_name))


def update_learning_collections():
    """Remove duplicates in the learning_{id} collections of the logs MongoDB
    database.
    """
    repo = MongoDBRepository.objects.get(repo_name="Vulture Internal Database")

    logger.info("Connecting to MongoDB")

    client = MongoDBClient(repo)
    con = client._get_connection()
    db_logs = con.logs

    try:
        logger.debug("Creating new collections")
        create_new_collections(db_logs)
    except Exception, e:
        logger.error("Something went wrong: some collections weren't processed: "
                     "backing up the database :")
        logger.exception(e)
        delete_new_learning_collections(db_logs)
        raise UpdateCrash("Failed to create new collections")

    try:
        transfer_new_collections(db_logs)
    except Exception, e:
        logger.exception(e)
        raise UpdateCrash("Something went wrong while transferring the new collections")



if __name__ == "__main__":
    try:
        logger.info("Executing the MongoDB migration script")

        cluster = Cluster.objects.get()
        current_node = cluster.get_current_node()

        if not current_node.is_mongodb_primary():
            logger.warning("This node is not a MongoDB master : Exiting.")
            sys_exit(1)

        logger.info("The main purpose is to remove the duplicates in each of the "
                    "learning_{id} collections in the logs MongoDB database")

        update_learning_collections()

        logger.info("The migrations has been completed successfully")

    except UpdateCrash, error:
        logger.error("Error while executing the MongoDB migration script")

    except Exception, error:
        logger.error("Error while executing the MongoDB migration script")
        logger.exception(error)

