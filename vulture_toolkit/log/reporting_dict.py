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
__author__ = "Thomas Fossati"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ = "Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = ''

from collections import OrderedDict

reporting_dicts = {
    "access": {
        "request_count": {
            "type": ["date_based", "multiple_series"],
            "mongo": {
                "$group": {
                    "_id": {
                        "year": {"$year": "$time"},
                        "month": {"$month": "$time"},
                        "series": "$http_code"
                    },
                    "value": {
                        "$sum": 1
                    }
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                },
                "$sort": OrderedDict([("name.year", 1),
                                      ("name.month", 1),
                                      ("name.day", 1),
                                      ("name.hour", 1),
                                      ("name.minute", 1)])
            },
            "elastic": {
                "aggs": {
                    "request_count": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": "day"
                        },
                        "aggs": {
                            "request_count": {
                                "terms": {
                                    "field": "http_code",
                                    "size": 500
                                }
                            }
                        }
                    }
                }
            }
        },
        "http_method": {
            "type": [],
            "mongo": {
                "$group": {
                    "_id": "$http_method",
                    "value": {
                        "$sum": 1
                    }
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                }
            },
            "elastic": {
                "aggs": {
                    "http_method": {
                        "terms": {
                            "field": "http_method",
                            "size": 2147483647
                        }
                    }
                }
            }
        },
        "static_requests": {
            "type": ["order_count"],
            "mongo": OrderedDict([
                ("$group", {
                    "_id": {
                        "uri": "$requested_uri",
                        "app": "$app_name"
                    },
                    "value": {
                        "$sum": 1
                    }
                }),
                ("$sort", {
                    "value": -1
                }),
                ("$limit", 100),
                ("$project", {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                })
            ]),
            "elastic": {
                "aggs": {
                    "static_requests": {
                        "terms": {
                            "field": "app_name",
                            "size": 100
                        },
                        "aggs": {
                            "static_requests": {
                                "terms": {
                                    "field": "requested_uri",
                                    "size": 100
                                }
                            }
                        }
                    }
                }
            }

        },
        "average_breceived": {
            "type": ["date_based", "average"],
            "mongo": {
                "$group": {
                    "_id": {
                        "year": {"$year": "$time"},
                        "month": {"$month": "$time"},
                    },
                    "value": {
                        "$avg": "$bytes_received"
                    }
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                },
                "$sort": OrderedDict([("name.year", 1),
                                      ("name.month", 1),
                                      ("name.day", 1),
                                      ("name.hour", 1),
                                      ("name.minute", 1)])
            },
            "elastic": {
                "aggs": {
                    "average_breceived": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": "day"
                        },
                        "aggs": {
                            "avg_bucket": {
                                "avg": {
                                    "field": "bytes_received"
                                }
                            }
                        }
                    }
                }
            }
        },
        "average_bsent": {
            "type": ["date_based", "average"],
            "mongo": {
                "$group": {
                    "_id": {
                        "year": {"$year": "$time"},
                        "month": {"$month": "$time"},
                    },
                    "value": {
                        "$avg": "$bytes_sent"
                    }
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                },
                "$sort": OrderedDict([("name.year", 1),
                                      ("name.month", 1),
                                      ("name.day", 1),
                                      ("name.hour", 1),
                                      ("name.minute", 1)])
            },
            "elastic": {
                "aggs": {
                    "average_bsent": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": "day"
                        },
                        "aggs": {
                            "avg_bucket": {
                                "avg": {
                                    "field": "bytes_sent"
                                }
                            }
                        }
                    }
                }
            }
        },
        "average_time": {
            "type": ["date_based", "average"],
            "mongo": {
                "$group": {
                    "_id": {
                        "year": {"$year": "$time"},
                        "month": {"$month": "$time"},
                    },
                    "value": {
                        "$avg": "$time_elapsed"
                    }  # µs to ms
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                },
                "$sort": OrderedDict([("name.year", 1),
                                      ("name.month", 1),
                                      ("name.day", 1),
                                      ("name.hour", 1),
                                      ("name.minute", 1)])
            },
            "elastic": {
                "aggs": {
                    "average_time": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": "day"
                        },
                        "aggs": {
                            "avg_bucket": {
                                "avg": {
                                    "field": "time_elapsed"
                                }
                            }
                        }
                    }
                }
            }
        },
        "UA_based": {
            "type": [],
            "mongo": {
                "$group": {
                    "_id": "$user_agent",
                    "value": {
                        "$sum": 1
                    }
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                }
            },
            "elastic": {
                "aggs": {
                    "UA_based": {
                        "terms": {
                            "field": "user_agent",
                            "size": 2147483647
                        }
                    }
                }
            }
        }
    },
    "security": {
        "request_count": {
            "type": ["date_based", "multiple_series"],
            "mongo": {
                "$group": {
                    "_id": {
                        "year": {"$year": "$time"},
                        "month": {"$month": "$time"},
                        "series": "$http_code"
                    },
                    "value": {
                        "$sum": 1
                    }
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                },
                "$sort": OrderedDict([("name.year", 1),
                                      ("name.month", 1),
                                      ("name.day", 1),
                                      ("name.hour", 1),
                                      ("name.minute", 1)])
            },
            "elastic": {
                "aggs": {
                    "request_count": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": "day"
                        },
                        "aggs": {
                            "request_count": {
                                "terms": {
                                    "field": "http_code",
                                    "size": 500
                                }
                            }
                        }
                    }
                }
            }
        },
        "average_score": {
            "type": ["date_based", "multiple_series", "average"],
            "mongo": {
                "$group": {
                    "_id": {
                        "year": {"$year": "$time"},
                        "month": {"$month": "$time"},
                        "series": "$http_code"
                    },
                    "value": {
                        "$avg": "$score"
                    }
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                },
                "$sort": OrderedDict([("name.year", 1),
                                      ("name.month", 1),
                                      ("name.day", 1),
                                      ("name.hour", 1),
                                      ("name.minute", 1)])
            },
            "elastic": {
                "aggs": {
                    "average_score": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": "day"
                        },
                        "aggs": {
                            "average_score": {
                                "terms": {
                                    "field": "http_code",
                                    "size": 2147483647
                                },
                                "aggs": {
                                    "avg_bucket": {
                                        "avg": {
                                            "field": "score"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "owasp_top10": {
            "type": ["regex", "multiple_series"],
            "mongo": OrderedDict([
                ("$match", {
                    "owasp_top10": {"$ne": "-"}
                }
                ),
                ("$group", {
                    "_id": "$http_code",
                    "owasps": {"$push": {"owasp": "$owasp_top10"}},
                    "value": {"$sum": 1}
                }
                ),
                ("$unwind", "$owasps"),
                ("$groupPip1", {
                    "_id": {
                        "name": "$_id",
                        "owasp": "$owasps"
                    },
                    "value": {"$sum": 1}
                }),
                ("$groupPip2", {
                    "_id": "$_id.name",
                    "value": {
                        "$push": {"name": "$_id.owasp.owasp", "value": "$value"}
                    }
                }),
                ("$project", {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                })
            ]),
            "elastic": {
                "query": {
                    "bool": {
                        "must_not": {
                            "term": {
                                "owasp_top10": "-"
                            }
                        }
                    }
                },
                "aggs": {
                    "owasp_top10": {
                        "terms": {
                            "field": "http_code"
                        },
                        "aggs": {
                            "owasp_top10": {
                                "terms": {
                                    "field": "owasp_top10",
                                    "size": 2147483647
                                }
                            }
                        }
                    }
                }
            }
        },
        "blocked_requests": {
            "type": ["regex"],
            "mongo": {
                "$match": {
                    "reasons": {"$ne": "-"}
                },
                "$group": {
                    "_id": "$reasons",
                    "value": {
                        "$sum": 1
                    }
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                }
            },
            "elastic": {
                "query": {
                    "bool": {
                        "must_not": {
                            "term": {
                                "reasons": "-"
                            }
                        }
                    }
                },
                "aggs": {
                    "blocked_requests": {
                        "terms": {
                            "field": "reasons",
                            "size": 2147483647
                        }
                    }
                }
            }
        },
        "reputation_tags": {
            "type": [],
            "mongo": OrderedDict([
                ("$match", {
                    "reputation": {"$ne": "-,-,-,-,-"}
                }
                ),
                ("$group", {
                    "_id": "$reputation",
                    "ips": {"$push": {"ip": "$src_ip"}},
                    "value": {"$sum": 1}
                }
                ),
                ("$unwind", "$ips"),
                ("$groupPip1", {
                    "_id": {
                        "reputation": "$_id",
                        "ips": "$ips",
                        "value": "$value"
                    },
                    "value": {"$sum": 1}
                }),
                ("$groupPip2", {
                    "_id": {
                        "reputation": "$_id.reputation",
                        "value": "$_id.value"
                    },
                    "ips": {
                        "$push": {
                            "ip": "$_id.ips.ip",
                            "value": "$value"
                        }
                    }
                }),
                ("$unwindPip1", "$ips"),
                ("$sort", {"ips.value": -1}),
                ("$groupPip3", {
                    "_id": "$_id",
                    "ips": {
                        "$push": "$ips"
                    }
                }),
                ("$project", {
                    "_id": 0,
                    "name": "$_id.reputation",
                    "value": "$_id.value",
                    "ips": {
                        "$slice": ["$ips", 20]
                    }})
            ]),
            "elastic": {
                "query": {
                    "bool": {
                        "must_not": {
                            "term": {
                                "reputation": "-,-,-,-,-"
                            }
                        }
                    }
                },
                "aggs": {
                    "reputation_tags": {
                        "terms": {
                            "field": "reputation"
                        },
                        "aggs": {
                            "reputation_tags": {
                                "terms": {
                                    "field": "src_ip",
                                    "size": 20
                                }
                            }
                        }
                    }
                }
            }
        }

    },
    "packet_filter": {
        "pf_traffic_in": {
            "type": ["date_based"],
            "mongo": OrderedDict([
                ("$match", {
                    "direction": {"$eq": "in"}
                }),
                ("$group", {
                    "_id": {
                        "year": {"$year": "$time"},
                        "month": {"$month": "$time"}
                    },
                    "value": {
                        "$sum": 1
                    }
                }),
                ("$project", {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                }),
                ("$sort", OrderedDict([("name.year", 1),
                                       ("name.month", 1),
                                       ("name.day", 1),
                                       ("name.hour", 1),
                                       ("name.minute", 1)]))
            ]),
            "elastic": {
                "query": {
                    "bool": {
                        "must": {
                            "term": {
                                "direction": "in"
                            }
                        }
                    }
                },
                "aggs": {
                    "pf_traffic_in": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": "day"
                        }
                    }
                }
            }
        },
        "pf_traffic_out": {
            "type": ["date_based"],
            "mongo": OrderedDict([
                ("$match", {
                    "direction": {"$eq": "out"}
                }),
                ("$group", {
                    "_id": {
                        "year": {"$year": "$time"},
                        "month": {"$month": "$time"}
                    },
                    "value": {
                        "$sum": 1
                    }
                }),
                ("$project", {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                }),
                ("$sort", OrderedDict([("name.year", 1),
                                       ("name.month", 1),
                                       ("name.day", 1),
                                       ("name.hour", 1),
                                       ("name.minute", 1)]))
            ]),
            "elastic": {
                "query": {
                    "bool": {
                        "must": {
                            "term": {
                                "direction": "out"
                            }
                        }
                    }
                },
                "aggs": {
                    "pf_traffic_out": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": "day"
                        }
                    }
                }
            }
        },
        "firewall_actions_in": {
            "type": [],
            "mongo": {
                "$match": {
                    "direction": {"$eq": "in"}
                },
                "$group": {
                    "_id": "$action",
                    "value": {
                        "$sum": 1
                    }
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                },
                "$sort": {"name": 1}
            },
            "elastic": {
                "query": {
                    "bool": {
                        "must": {
                            "term": {
                                "direction": "in"
                            }
                        }
                    }
                },
                "aggs": {
                    "firewall_actions_in": {
                        "terms": {
                            "field": "action"
                        }
                    }
                }
            }
        },
        "firewall_actions_out": {
            "type": [],
            "mongo": {
                "$match": {
                    "direction": {"$eq": "out"}
                },
                "$group": {
                    "_id": "$action",
                    "value": {
                        "$sum": 1
                    }
                },
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                },
                "$sort": {"name": 1}
            },
            "elastic": {
                "query": {
                    "bool": {
                        "must": {
                            "term": {
                                "direction": "out"
                            }
                        }
                    }
                },
                "aggs": {
                    "firewall_actions_out": {
                        "terms": {
                            "field": "action"
                        }
                    }
                }
            }
        },
        "top_ip_src_in": {
            "type": [],
            "mongo": OrderedDict([
                ("$match", {"direction": {"$eq": "in"}}),
                ("$group", {
                    "_id": "$src_ip",
                    "value": {
                        "$sum": 1
                    }
                }),
                ("$project", {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                }),
                ("$sort", {"value": -1}),
                ("$limit", 100)
            ]),
            "elastic": {
                "query": {
                    "bool": {
                        "must": {
                            "term": {
                                "direction": "in"
                            }
                        }
                    }
                },
                "aggs": {
                    "top_ip_src_in": {
                        "terms": {
                            "field": "src_ip",
                            "size": 100
                        }
                    }
                }
            }
        },
        "top_ip_src_out": {
            "type": [],
            "mongo": OrderedDict([
                ("$match", {"direction": {"$eq": "out"}}),
                ("$group", {
                    "_id": "$src_ip",
                    "value": {
                        "$sum": 1
                    }
                }),
                ("$project", {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                }),
                ("$sort", {"value": -1}),
                ("$limit", 100)
            ]),
            "elastic": {
                "query": {
                    "bool": {
                        "must": {
                            "term": {
                                "direction": "out"
                            }
                        }
                    }
                },
                "aggs": {
                    "top_ip_src_out": {
                        "terms": {
                            "field": "src_ip",
                            "size": 100
                        }
                    }
                }
            }
        },
        "top_ip_dst_in": {
            "type": [],
            "mongo": OrderedDict([
                ("$match", {"direction": {"$eq": "in"}}),
                ("$group", {
                    "_id": "$dst_ip",
                    "value": {
                        "$sum": 1
                    }
                }),
                ("$project", {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                }),
                ("$sort", {"value": -1}),
                ("$limit", 100)
            ]),
            "elastic": {
                "query": {
                    "bool": {
                        "must": {
                            "term": {
                                "direction": "in"
                            }
                        }
                    }
                },
                "aggs": {
                    "top_ip_dst_in": {
                        "terms": {
                            "field": "dst_ip",
                            "size": 100
                        }
                    }
                }
            }
        },
        "top_ip_dst_out": {
            "type": [],
            "mongo": OrderedDict([
                ("$match", {"direction": {"$eq": "out"}}),
                ("$group", {
                    "_id": "$dst_ip",
                    "value": {
                        "$sum": 1
                    }
                }),
                ("$project", {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                }),
                ("$sort", {"value": -1}),
                ("$limit", 100)
            ]),
            "elastic": {
                "query": {
                    "bool": {
                        "must": {
                            "term": {
                                "direction": "out"
                            }
                        }
                    }
                },
                "aggs": {
                    "top_ip_dst_out": {
                        "terms": {
                            "field": "dst_ip",
                            "size": 100
                        }
                    }
                }
            }
        },
        "top_ports_in": {
            "type": ["multiple_series"],
            "mongo": OrderedDict([
                ("$match", {
                    "dst_port": {"$ne": None},
                    "direction": {"$eq": "in"}
                }),
                ("$group", {
                    "_id": "$dst_port",
                    "actions": {"$push": {"action": "$action"}},
                    "value": {"$sum": 1}
                }),
                ('$sort', {'value': -1}),
                ("$limit", 20),
                ("$unwind", "$actions"),
                ("$groupPip1", {
                    "_id": {
                        "name": "$_id",
                        "action": "$actions"
                    },
                    "value": {"$sum": 1}
                }),
                ("$groupPip2", {
                    "_id": "$_id.name",
                    "value": {
                        "$push": {"name": "$_id.action.action", "value": "$value"}
                    }
                }),
                ("$project", {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                })]),
            "elastic": {
                "query": {
                    "bool": {
                        "must": {
                            "term": {
                                "direction": "in"
                            }
                        }
                    }
                },
                "aggs": {
                    "top_ports_in": {
                        "terms": {
                            "field": "dst_port",
                            "size": 20
                        },
                        "aggs": {
                            "top_ports_in": {
                                "terms": {
                                    "field": "action"
                                }
                            }
                        }
                    }
                }
            }
        },
        "top_ports_out": {
            "type": ["multiple_series"],
            "mongo": OrderedDict([
                ("$match", {
                    "dst_port": {"$ne": None},
                    "direction": {"$eq": "out"}
                }),
                ("$group", {
                    "_id": "$dst_port",
                    "actions": {"$push": {"action": "$action"}},
                    "value": {"$sum": 1}
                }),
                ('$sort', {'value': -1}),
                ("$limit", 20),
                ("$unwind", "$actions"),
                ("$groupPip1", {
                    "_id": {
                        "name": "$_id",
                        "action": "$actions"
                    },
                    "value": {"$sum": 1}
                }),
                ("$groupPip2", {
                    "_id": "$_id.name",
                    "value": {
                        "$push": {"name": "$_id.action.action", "value": "$value"}
                    }
                }),
                ("$project", {
                    "_id": 0,
                    "name": "$_id",
                    "value": {"$ifNull": ["$value", 0]}
                })]),
            "elastic": {
                "query": {
                    "bool": {
                        "must": {
                            "term": {
                                "direction": "out"
                            }
                        }
                    }
                },
                "aggs": {
                    "top_ports_out": {
                        "terms": {
                            "field": "dst_port",
                            "size": 20
                        },
                        "aggs": {
                            "top_ports_out": {
                                "terms": {
                                    "field": "action"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


def type_of_dict(function, type_dict):
    for reporting_dict in reporting_dicts.values():
        try:
            return type_dict in reporting_dict[function]['type']
        except KeyError:
            pass
    return False


def get_function_dict(function):
    for reporting_dict in reporting_dicts.values():
        try:
            return reporting_dict[function]
        except KeyError:
            pass
    return None
