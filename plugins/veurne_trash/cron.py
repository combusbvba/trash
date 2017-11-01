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

import datetime
import logging

from babel.dates import format_date

from framework.bizz.job import run_job
from google.appengine.ext import ndb
from google.appengine.ext.ndb.query import QueryOptions
from plugins.veurne_trash.localizer import translate_key
from plugins.veurne_trash.models import UserLocation
from plugins.veurne_trash.plugin_bizz import get_api_collections, update_user_data, send_collection_message
from plugins.veurne_trash.plugin_utils import today
from plugins.rogerthat_api.models.settings import RogerthatSettings
from framework.utils import now
import webapp2


class BroadcastNotificationsHandler(webapp2.RequestHandler):

    def get(self):
#        run_job(_query_settings, [], _worker_settings, [])
        _worker_settings(RogerthatSettings.query().get())

def _worker_settings(settings):
    tomorrow = now() + 86400
    run_job(_query_locations, [settings.sik, tomorrow], _worker_locations, [])


def _query_locations(sik, epoch):
    return UserLocation.query(namespace=UserLocation.create_namespace(sik), default_options=QueryOptions(
                      keys_only=True)).filter(UserLocation.next_collection < epoch)


def _worker_locations(ul_key):
    ul = ul_key.get()
    now_ = now()
    tomorrow = now_ + 86400
    if ul.next_collection > tomorrow:
        logging.error("broadcast collection message failed double run")
        return

    collections = get_api_collections(ul.sik, ul.street_number, ul.house_number, ul.house_bus, today())
    names = []
    for collection in collections:
        if now_ > collection.epoch:
            pass
        elif collection.epoch == ul.next_collection:
            if collection.activity.number in ul.notifications:
                names.append(collection.activity.name)
        elif collection.epoch > ul.next_collection:
            next_collection = collection.epoch
            break

    cd = datetime.datetime.fromtimestamp(ul.next_collection)
    d = format_date(cd, locale="nl_BE", format='d MMM')

    def trans():
        user_location = ul_key.get()
        # user_data was more than 7 days old, update collections (maybe outdated)
        if now_ >= (user_location.user_data_epoch + 7 * 86400):
            user_location.user_data_epoch = now_
            update_user_data(ul.sik, user_location.service_identity, user_location.email, user_location.app_id, user_location.address, user_location.notifications, collections)

        if names:
            message = translate_key(u"nl", u"collection_broadcast", date=d, collections="\n-".join(names))
            send_collection_message(ul.sik, user_location.service_identity, user_location.email, user_location.app_id, message)

        user_location.next_collection = next_collection
        user_location.put()
    ndb.transaction(trans)
