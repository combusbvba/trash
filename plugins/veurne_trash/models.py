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

from google.appengine.ext import ndb
from plugins.veurne_trash import plugin_consts



class UserLocation(ndb.Model):
    service_identity = ndb.StringProperty()
    address = ndb.StringProperty(indexed=False)
    street_number = ndb.IntegerProperty(indexed=False)
    house_number = ndb.IntegerProperty(indexed=False)
    house_bus = ndb.StringProperty(indexed=False)
    notifications = ndb.IntegerProperty(indexed=False, repeated=True)
    user_data_epoch = ndb.IntegerProperty(indexed=False)
    next_collection = ndb.IntegerProperty()

    @property
    def sik(self):
        return self.key.namespace().split("-")[1].decode('utf8')

    @property
    def email(self):
        return self.key.id().split(":")[0].decode('utf8')

    @property
    def app_id(self):
        return self.key.id().split(":")[1].decode('utf8')

    @classmethod
    def create_key(cls, sik, email, app_id):
        return ndb.Key(cls, "%s:%s" % (email, app_id), namespace=UserLocation.create_namespace(sik))

    @staticmethod
    def get_by_info(sik, email, app_id):
        return UserLocation.create_key(sik, email, app_id).get()

    @staticmethod
    def create_namespace(sik):
        return "%s-%s" % (plugin_consts.NAMESPACE, sik)
