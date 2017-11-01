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
from bs4 import BeautifulSoup as BS
import urllib2
import sys
import HTMLParser
from icalendar import Calendar, Event, vDatetime

from google.appengine.api import urlfetch
from google.appengine.ext import deferred, ndb
from mcfw.cache import cached
from mcfw.rpc import returns, arguments, serialize_complex_value
from plugins.veurne_trash.models import UserLocation
from plugins.veurne_net_trash.plugin_consts import HTTPS_BASE_URL, ROGERTHAT_EXCEPTION_CODE_SERVICE_USER_NOT_FOUND, \
    ROGERTHAT_EXCEPTION_CODE_MESSAGE_USER_NOT_FOUNDS
from plugins.veurne_trash.plugin_utils import today
from plugins.veurne_trash.to import HouseTO, StreetTO, ActivityTO, CollectionTO
from plugins.rogerthat_api.api import system, messaging, RogerthatApiException
from plugins.rogerthat_api.to import MemberTO
from plugins.rogerthat_api.models.settings import RogerthatSettings
from framework.utils import guid, now

@returns(unicode)
@arguments(sik=unicode)
def get_api_login_token(sik):

    args = dict()
    url = "%slogin.json?%s" % (HTTPS_BASE_URL, urlencode(args))

    result = urlfetch.fetch(url=url, method=urlfetch.POST, headers=get_api_headers(sik), deadline=55)
    logging.info(result.content)

    if result.status_code != 200:
        raise Exception("Failed when loading get_api_login_token")

    json_response = json.loads(result.content)
    return unicode(json_response["loginkey"])


@returns([StreetTO])
@arguments(sik=unicode)
def get_api_streets(sik):

    args = dict()
    URL_POST = 'http://www.ivvo.be/ahah-gemeente-exposed-callback'

    sdata = {}
    sdata['field_gemeente_value'] = 'Veurne'
    sdata['field_straat_value'] = ''
    sdata['field_straatnrvan_value'] = ''
    sdata['field_straatnrtot_value'] = ''

    sdata = urlencode(sdata)

    result = urlfetch.fetch(url=URL_POST, deadline=55, payload=sdata, method=2)

    if result.status_code != 200:
        raise Exception("Failed when loading get_api_streets")

    decodedcontent = result.content.decode('unicode_escape')

    soup = BS(decodedcontent, 'html.parser')
    contents = [x.text.encode('cp1252').decode('utf8') for x in soup.find(id="field_straat_value").find_all('option')]
    contents = list(filter(None, contents))

    lijstNRS = [x for x in range(0,len(contents))]
    lijstCompleet = [{'s': straat, 'nr': nummer} for straat, nummer in zip(contents, lijstNRS)]
    logging.info(lijstCompleet)

    json_response = json.loads(json.dumps(lijstCompleet))
    return [StreetTO.fromObj(s) for s in json_response]


@returns([HouseTO])
@arguments(sik=unicode, street_number=long)
def get_api_houses(sik, street_number):
    args = dict()

    lijstNRS = [x for x in range(1,800)]
    lijstBUS = ["" for w in range(1,800)]
    lijstCompleet = [{'h': huisnr, 't': bus} for huisnr, bus in zip(lijstNRS, lijstBUS)]

    json_response = json.loads(json.dumps(lijstCompleet))

    return [HouseTO.fromObj(s) for s in json_response]


@returns([ActivityTO])
@arguments(sik=unicode)
def get_api_activities(sik):
    args = dict()

    lijstAFVAL = []
    lijstAFVAL.append([7 , 'Grofvuil op afroep'])
    lijstAFVAL.append([21 , 'Restafval'])
    lijstAFVAL.append([23 , 'Kerstboom'])
    lijstAFVAL.append([27 , 'Papier en karton Zone 1'])
    lijstAFVAL.append([37 , 'Papier en karton Zone 2'])
    lijstAFVAL.append([47 , 'Papier en karton Zone 3'])
    lijstAFVAL.append([28 , 'PMD'])
    lijstAFVAL.append([29 , 'Snoeihout op afroep'])
    lijstAFVAL.append([30 , 'Textiel'])
    lijstAFVAL.append([31 , 'Oude metalen op afroep'])
    lijstAFVAL.append([32 , 'GFT'])
    lijstCompleet = [{'nr': nummers, 's': beschrijvingAfval} for nummers, beschrijvingAfval in lijstAFVAL]

    json_response = json.loads(json.dumps(lijstCompleet))

    return [ActivityTO.fromObj(s) for s in json_response]


@returns([CollectionTO])
@arguments(sik=unicode, street_name=unicode, house_number=long, house_bus=unicode, time_from=long)
def get_api_collections(sik, street_name, house_number, house_bus, time_from):
    args = dict()
    args["straatnaam"] = street_name
    args["huisnummer"] = house_number
    args["toevoeging"] = house_bus

    d_from = datetime.date.fromtimestamp(time_from)

    args["van"] = u"%s/%s/%s" % (d_from.day, d_from.month, d_from.year)
    args["tem"] = u"31/12/%s" % d_from.year
    BASIS_URL = 'http://www.ivvo.be/icallink/?'
    f = { 'field_gemeente_value' : 'Veurne', 'field_straat_value' : street_name.encode('utf-8'), 'field_straatnrvan_value' : house_number}

    REQ_URL = BASIS_URL + urlencode(f)

    try:
        result = urlfetch.fetch(url=REQ_URL, deadline=55)
        if result.status_code == 200:
            logging.info(result.content)
        else:
            logging.error("failed to load get_api_collections")
            raise Exception("Het laden van de afvalkalender is mislukt.")
    except urlfetch.Error:
        logging.error('Caught exception fetching url')
        raise Exception("Het laden van de afvalkalender is mislukt.")

    cal = Calendar.from_ical(result.content)
    lijst1 = []
    lijst2 = []
    for event in cal.walk('vevent'):

        date = event.get('dtstart')
        summary = event.get('summary')
        summaryID = 33
        lijst1.append(str(date.dt))
        if str(summary)=="Grofvuil op afroep": summaryID = 7
        if str(summary)=="Restafval": summaryID=21
        if str(summary)=="Kerstboom": summaryID=23
        if str(summary)=="Papier en karton Zone 1": summaryID=27
        if str(summary)=="Papier en karton Zone 2": summaryID=37
        if str(summary)=="Papier en karton Zone 3": summaryID=47
        if str(summary)=="PMD": summaryID=28
        if str(summary)=="Snoeihout op afroep": summaryID=29
        if str(summary)=="Textiel": summaryID=33
        if str(summary)=="Oude metalen op afroep": summaryID=31
        if str(summary)=="GFT": summaryID=32
        lijst2.append(summaryID)
    lijstCompleet = [{'d': datum, 'a': afval} for datum, afval in zip(lijst1, lijst2)]

    activities = {}
    for a in get_api_activities(sik):
        activities[a.number] = a
    json_response = json.loads(json.dumps(lijstCompleet))

    collections = [CollectionTO.fromObj(s, activities[s["a"]]) for s in json_response]

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
        collections = get_api_collections(sik, street_name, house_number, house_bus, today())

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
    settings = RogerthatSettings.create_key(sik).get()
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
    settings = RogerthatSettings.create_key(sik).get()
    si = system.get_identity(settings.api_key, service_identity)
    return si.description_branding


def send_collection_message(sik, service_identity, email, app_id, message):
    json_rpc_id = guid()
    deferred.defer(_send_collection_message, sik, service_identity, email, app_id, message, json_rpc_id, _transactional=ndb.in_transaction())


def _send_collection_message(sik, service_identity, email, app_id, message, json_rpc_id):
    settings = RogerthatSettings.create_key(sik).get()
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
