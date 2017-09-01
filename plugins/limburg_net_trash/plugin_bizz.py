# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.2@@

import base64
import datetime
import json
import logging
from urllib import urlencode

from google.appengine.api import urlfetch
from google.appengine.ext import deferred, ndb
from mcfw.cache import cached
from mcfw.rpc import returns, arguments, serialize_complex_value
from plugins.limburg_net_trash.models import UserLocation, Settings
from plugins.limburg_net_trash.plugin_consts import HTTPS_BASE_URL, ROGERTHAT_EXCEPTION_CODE_SERVICE_USER_NOT_FOUND, \
    ROGERTHAT_EXCEPTION_CODE_MESSAGE_USER_NOT_FOUNDS
from plugins.limburg_net_trash.plugin_utils import today
from plugins.limburg_net_trash.to import HouseTO, StreetTO, ActivityTO, CollectionTO
from plugins.rogerthat_api.api import system, messaging, RogerthatApiException
from plugins.rogerthat_api.to import MemberTO
from framework.utils import guid, now


@returns(Settings)
@arguments(sik=unicode)
def get_settings(sik):
    return Settings.create_key(sik).get()


@cached(1, request=True, memcache=False)
@returns(Settings)
@arguments(sik=unicode)
def get_settings_cached(sik):
    return get_settings(sik)


@returns(bool)
@arguments(sik=unicode)
def is_valid_sik(sik):
    if get_settings_cached(sik):
        return True
    return False


@cached(1, request=True, memcache=False)
@returns(dict)
@arguments(sik=unicode)
def get_api_headers(sik):
    settings = get_settings_cached(sik)
    base64string = base64.encodestring('%s:%s' % (settings.https_username, settings.https_pwd))[:-1]
    headers = {}
    headers['Authorization'] = "Basic %s" % base64string
    return headers


@cached(1, lifetime=3500, request=False, memcache=True)
@returns(unicode)
@arguments(sik=unicode)
def get_api_login_token(sik):
    settings = get_settings_cached(sik)
    args = dict()
    args["servicegebruiker"] = settings.service_user
    args["servicepwd"] = settings.service_pwd
    url = "%slogin.json?%s" % (HTTPS_BASE_URL, urlencode(args))

    result = urlfetch.fetch(url=url, method=urlfetch.POST, headers=get_api_headers(sik), deadline=55)
    logging.info(result.content)

    if result.status_code != 200:
        raise Exception("Failed when loading get_api_login_token")

    json_response = json.loads(result.content)
    return unicode(json_response["loginkey"])


@cached(1, lifetime=86400, request=False, memcache=True)
@returns([StreetTO])
@arguments(sik=unicode)
def get_api_streets(sik):
    settings = get_settings_cached(sik)
    args = dict()
    args["loginkey"] = get_api_login_token(sik)
    args["niscode"] = settings.nis_code
    url = "%sgeef_straten_van_gemeente.json?%s" % (HTTPS_BASE_URL, urlencode(args))
    result = urlfetch.fetch(url=url, headers=get_api_headers(sik), deadline=55)
    logging.info(result.content)

    if result.status_code != 200:
        raise Exception("Failed when loading get_api_streets")

    json_response = json.loads(result.content)
    return [StreetTO.fromObj(s) for s in json_response["l"]]


@cached(1, lifetime=86400, request=False, memcache=True)
@returns([HouseTO])
@arguments(sik=unicode, street_number=long)
def get_api_houses(sik, street_number):
    args = dict()
    args["loginkey"] = get_api_login_token(sik)
    args["straatnummer"] = street_number
    url = "%sgeef_huisnummers_van_straat.json?%s" % (HTTPS_BASE_URL, urlencode(args))
    result = urlfetch.fetch(url=url, headers=get_api_headers(sik), deadline=55)
    logging.info(result.content)

    if result.status_code != 200:
        raise Exception("Failed when loading get_api_houses")

    json_response = json.loads(result.content)
    return [HouseTO.fromObj(s) for s in json_response["l"]]


@cached(1, lifetime=86400, request=False, memcache=True)
@returns([ActivityTO])
@arguments(sik=unicode)
def get_api_activities(sik):
    args = dict()
    args["loginkey"] = get_api_login_token(sik)
    url = "%sgeef_activiteiten.json?%s" % (HTTPS_BASE_URL, urlencode(args))
    result = urlfetch.fetch(url=url, headers=get_api_headers(sik), deadline=55)
    logging.info(result.content)

    if result.status_code != 200:
        raise Exception("Failed when loading get_api_activities")

    json_response = json.loads(result.content)
    return [ActivityTO.fromObj(s) for s in json_response["l"]]


@cached(1, lifetime=86400, request=False, memcache=True)
@returns([CollectionTO])
@arguments(sik=unicode, street_number=long, house_number=long, house_bus=unicode, time_from=long)
def get_api_collections(sik, street_number, house_number, house_bus, time_from):
    settings = get_settings_cached(sik)
    args = dict()
    args["loginkey"] = get_api_login_token(sik)
    args["niscode"] = settings.nis_code
    args["straatnummer"] = street_number
    args["huisnummer"] = house_number
    args["toevoeging"] = house_bus

    d_from = datetime.date.fromtimestamp(time_from)

    args["van"] = u"%s/%s/%s" % (d_from.day, d_from.month, d_from.year)
    args["tem"] = u"31/12/%s" % d_from.year
    url = "%sgeef_ophalingen.json?%s" % (HTTPS_BASE_URL, urlencode(args))
    result = urlfetch.fetch(url=url, headers=get_api_headers(sik), deadline=55)
    logging.info(result.content)

    if result.status_code != 200:
        logging.error("failed to load get_api_collections")
        raise Exception("Het laden van de afvalkalender is mislukt.")

    activities = {}
    for a in get_api_activities(sik):
        activities[a.number] = a
    json_response = json.loads(result.content)
    if json_response["errcode"] == 1:
        logging.error("get_api_collections returned an error")
        raise Exception("Het laden van de afvalkalender is mislukt.")
    elif json_response["errcode"] == 2:
        logging.error("get_api_collections returned an error")
        raise Exception(json_response["err"])

    collections = [CollectionTO.fromObj(s, activities[s["a"]]) for s in json_response["l"] if not s["c"]]

    if d_from.month >= 12:
        args["van"] = u"1/1/%s" % (d_from.year + 1)
        args["tem"] = u"31/12/%s" % (d_from.year + 1)
        url = "%sgeef_ophalingen.json?%s" % (HTTPS_BASE_URL, urlencode(args))
        result = urlfetch.fetch(url=url, headers=get_api_headers(sik), deadline=55)
        logging.info(result.content)

        if result.status_code != 200:
            logging.error("failed to load get_api_collections for next year")
            raise Exception("Het laden van de afvalkalender is mislukt.")

        json_response = json.loads(result.content)
        try:
            collections.extend([CollectionTO.fromObj(s, activities[s["a"]]) for s in json_response["l"] if not s["c"]])
        except:
            logging.exception("Failed when loading get_api_collections for next year")

    return collections


def get_streets(sik, service_identity, email, app_id, params):
    try:
        r = get_api_streets(sik)
        return {"result": json.dumps(serialize_complex_value(r, StreetTO, True)),
                "error": None}
    except:
        logging.exception(u"get_api_streets failed")
        return {"result": None,
                "error": u"get_api_streets failed"}


def get_street_numbers(sik, service_identity, email, app_id, params):
    try:
        jsondata = json.loads(params)
        r = get_api_houses(sik, long(jsondata["streetnumber"]))
        return {"result": json.dumps(serialize_complex_value(r, HouseTO, True)),
                "error": None}
    except:
        logging.exception(u"get_street_numbers failed")
        return {"result": None,
                "error": u"get_street_numbers failed"}


def set_location(sik, service_identity, email, app_id, params):
    try:
        jsondata = json.loads(params)
        street_number = long(jsondata['info']['street']['number'])
        street_name = jsondata['info']['street']['name']
        house_number = long(jsondata['info']['house']['number'])
        house_bus = jsondata['info']['house']['bus']
        collections = get_api_collections(sik, street_number, house_number, house_bus, today())
    except Exception, ex:
        return {"result": None,
                "error": ex.message}

    ul_key = UserLocation.create_key(sik, email, app_id)
    ul = ul_key.get()
    if not ul:
        ul = UserLocation(key=ul_key)
        ul.notifications = []
    ul.service_identity = service_identity
    ul.address = u"%s %s%s" % (street_name, house_number, house_bus)
    ul.street_number = street_number
    ul.house_number = house_number
    ul.house_bus = house_bus
    ul.user_data_epoch = now()
    ul.next_collection = collections[0].epoch
    ul.put()

    update_user_data(sik, service_identity, email, app_id, ul.address, ul.notifications, collections)

    return {"result": u"Location was set",
            "error": None}


def update_user_data(sik, service_identity, email, app_id, address, notifications, collections):
    deferred.defer(_update_user_data, sik, service_identity, email, app_id, address, notifications, collections, _transactional=ndb.in_transaction())


def _update_user_data(sik, service_identity, email, app_id, address, notifications, collections):
    settings = get_settings_cached(sik)
    user_data = dict()
    user_data["trash"] = {}
    user_data["trash"]["address"] = address
    activities = {}
    for collection in collections:
        activities[collection.activity.number] = collection.activity

    user_data["trash"]["collections"] = serialize_complex_value(collections, CollectionTO, True)
    user_data["trash"]["notifications"] = notifications
    user_data["trash"]["notification_types"] = serialize_complex_value(sorted(activities.values(), key=lambda a: a.name), ActivityTO, True)

    try:
        system.put_user_data(settings.api_key, email, app_id, user_data, service_identity)
    except RogerthatApiException, e:
        if e.code != ROGERTHAT_EXCEPTION_CODE_SERVICE_USER_NOT_FOUND:
            raise e
        logging.debug("Ignoring _update_user_data user de-friended")


def set_notifications(sik, service_identity, email, app_id, params):
    jsondata = json.loads(params)
    ul = UserLocation.get_by_info(sik, email, app_id)
    ul.notifications = jsondata['notifications']
    ul.put()

    return {"result": u"Notifications are updated",
            "error": None}


@cached(1, lifetime=600, request=False, memcache=True)
@returns(unicode)
@arguments(sik=unicode, service_identity=unicode)
def get_branding_key(sik, service_identity):
    settings = get_settings_cached(sik)
    si = system.get_identity(settings.api_key, service_identity)
    return si.description_branding


def send_collection_message(sik, service_identity, email, app_id, message):
    json_rpc_id = guid()
    deferred.defer(_send_collection_message, sik, service_identity, email, app_id, message, json_rpc_id, _transactional=ndb.in_transaction())


def _send_collection_message(sik, service_identity, email, app_id, message, json_rpc_id):
    settings = get_settings_cached(sik)
    member = MemberTO()
    member.member = email
    member.app_id = app_id
    member.alert_flags = 2
    try:

        messaging.send(settings.api_key, None, message, [], 1, [member], get_branding_key(sik, service_identity), None, json_rpc_id=json_rpc_id)
    except RogerthatApiException, e:
        if e.code != ROGERTHAT_EXCEPTION_CODE_MESSAGE_USER_NOT_FOUNDS:
            raise e
        logging.debug("Ignoring _send_collection_message user de-friended")
