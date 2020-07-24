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
__author__ = "Kevin Guillemot, Jérémie Jourdin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "3.0.0"
__maintainer__ ="Vulture Project"
__email__ = "contact@vultureproject.org"
__doc__ = 'Django views to display Self-service portal'



#import sys
#sys.path.append("/home/vlt-gui/vulture/portal")


# Django system imports
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseServerError, HttpResponseForbidden

# Django project imports
from portal.system.self_actions import SELFService, SELFServiceChange, SELFServiceLogout, SELFServiceLost
from vulture_toolkit.auth.exceptions import AuthenticationError, ChangePasswordError
from portal.views.responses import response_failure, response_success

# Required exceptions imports
from django.utils.datastructures     import MultiValueDictKeyError
from ldap                            import LDAPError
from portal.system.exceptions        import PasswordMatchError, RedirectionNeededError
from pymongo.errors                  import PyMongoError
from redis                           import ConnectionError as RedisConnectionError
from smtplib                         import SMTPException
from sqlalchemy.exc                  import DBAPIError

# Extern modules imports


# Logger configuration
import logging
logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('portal_authentication')




def self(request, token_name=None, proxy_app_id=None, action=None):

    """ Handle Vulture Self-Service portal
    :param request: Django request object
    :returns: Self-service portal
    """

    action_classes = {
        'change' : SELFServiceChange,
        'lost'   : SELFServiceLost,
        'logout' : SELFServiceLogout,
        None     : SELFService
    }


    try:
        Action = action_classes[action](proxy_app_id, token_name)

    except RedirectionNeededError as e:
        return HttpResponseRedirect(e.redirect_url)

    except RedisConnectionError as e:
        # Redis connection error
        logger.error("PORTAL::log_in: Unable to connect to Redis server : {}".format(str(e)))
        return response_failure(HttpResponseServerError(),action)

    # If assertionError : Forbidden
    except AssertionError as e:
        logger.error("PORTAL::log_in: AssertionError while trying to create Authentication : ".format(e))
        return response_failure(HttpResponseForbidden(), action)

    except Exception as e:
        logger.error("Unknown error occured while retrieving user informations :")
        logger.exception(e)
        return response_failure(HttpResponseForbidden(), action)


    try:
        credential = Action.retrieve_credentials(request)
        if not action:
            result = Action.perform_action()
            logger.info("SELF::main: List of apps successfully retrieven")
            return response_success(Action.main_response(request, result), "list_apps")
        else:
            return response_success(Action.message_response(Action.perform_action(request, credential)), action)

    # Redis connection error
    except RedisConnectionError as e:
        logger.error("PORTAL::log_in: Unable to connect to Redis server : {}".format(str(e)))
        return response_failure(HttpResponseServerError(), action)

    # If assertionError : Forbidden
    except AssertionError as e:
        logger.error("PORTAL::log_in: AssertionError while trying to create Authentication : '{}'".format(e))
        return response_failure(HttpResponseForbidden(e), action)

    except (DBAPIError, LDAPError, PyMongoError) as e:
        logger.error("SELF::self: Failed to update password :".format(e))
        logger.exception(e)
        return response_failure(Action.ask_credentials_response(request, action, "<b> Database error </b> <br> "
                                                                "Please contact your administrator"), action)

    except PasswordMatchError as e:
        logger.error("SELF::self: Validation form error: '{}'".format(e))
        return response_failure(Action.ask_credentials_response(request, action, e), action)

    except (ChangePasswordError, AuthenticationError) as e:
        logger.error("SELF::self: Authentication or credentials error : '{}'".format(e))
        return response_failure(Action.ask_credentials_response(request, action, "Authentication failure."), action)

    except MultiValueDictKeyError as e:
        if request.method == "GET":
            return Action.ask_credentials_response(request, action, "")
        else:
            logger.error("SELF::self: Field missing : '{}'".format(e))
            return Action.ask_credentials_response(request, action, "Field missing : "+str(e))

    except SMTPException as e:
        return response_failure(Action.ask_credentials_response(request, action, str(e)), action)

    except KeyError as e:
        logger.exception(e)
        return response_failure(HttpResponseForbidden(), action)

    except Exception as e:
        logger.error(type(e))
        logger.exception(e)
        return response_failure(Action.message_response("An unknown error occured <br><b> Please contact your admninistrator</b>"), action)
