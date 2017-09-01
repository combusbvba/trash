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

from plugins.limburg_net_trash.plugin_utils import get_epoch_from_datetime
from mcfw.properties import long_property, unicode_property, typed_property
from mcfw.serialization import register, deserializer, ds_unicode, serializer, s_unicode, s_long, get_list_serializer, \
    ds_long, get_list_deserializer, List


class StreetTO(object):
    number = long_property('1')
    name = unicode_property('2')

    @classmethod
    def fromObj(cls, obj):
        to = cls()
        to.number = obj["nr"]
        to.name = obj["s"]
        return to

@deserializer
def _ds_street_to(stream, version):
    to = StreetTO()
    to.number = ds_long(stream)
    to.name = ds_unicode(stream)
    return to

@serializer
def _s_street_to(stream, to):
    s_long(stream, to.number)
    s_unicode(stream, to.name)

def _s_street_list(stream, l):
    s_long(stream, 1)
    f = get_list_serializer(_s_street_to)
    f(stream, l)

def _ds_street_list(stream):
    l = list()
    version = ds_long(stream)
    f = get_list_deserializer(_ds_street_to, True)
    for to in f(stream, version):
        l.append(to)
    return l

register(List(StreetTO), _s_street_list, _ds_street_list)


class HouseTO(object):
    number = long_property('1')
    bus = unicode_property('2')

    @classmethod
    def fromObj(cls, obj):
        to = cls()
        to.number = obj["h"]
        to.bus = obj["t"]
        return to

@deserializer
def _ds_house_to(stream, version):
    to = HouseTO()
    to.number = ds_long(stream)
    to.bus = ds_unicode(stream)
    return to

@serializer
def _s_house_to(stream, to):
    s_long(stream, to.number)
    s_unicode(stream, to.bus)

def _s_house_list(stream, l):
    s_long(stream, 1)
    f = get_list_serializer(_s_house_to)
    f(stream, l)

def _ds_house_list(stream):
    l = list()
    version = ds_long(stream)
    f = get_list_deserializer(_ds_house_to, True)
    for to in f(stream, version):
        l.append(to)
    return l

register(List(HouseTO), _s_house_list, _ds_house_list)

CURRENT_ACTIVITY_VERSION = 1
class ActivityTO(object):
    number = long_property('1')
    name = unicode_property('2')

    @classmethod
    def fromObj(cls, obj):
        to = cls()
        to.number = obj["nr"]
        to.name = obj["s"]
        if to.name == u"grofvuil":
            to.name = u"grofvuil (enkel op aanvraag)"

        return to

@deserializer
def _ds_activity_to(stream, version):
    to = ActivityTO()
    to.number = ds_long(stream)
    to.name = ds_unicode(stream)
    return to

@serializer
def _s_activity_to(stream, to):
    s_long(stream, to.number)
    s_unicode(stream, to.name)

def _s_activity_list(stream, l):
    s_long(stream, CURRENT_ACTIVITY_VERSION)
    f = get_list_serializer(_s_activity_to)
    f(stream, l)

def _ds_activity_list(stream):
    l = list()
    version = ds_long(stream)
    f = get_list_deserializer(_ds_activity_to, True)
    for to in f(stream, version):
        l.append(to)
    return l

register(List(ActivityTO), _s_activity_list, _ds_activity_list)


class CollectionTO(object):
    epoch = long_property('1')
    year = long_property('2')
    month = long_property('3')
    day = long_property('4')
    activity = typed_property('5', ActivityTO, False)

    @classmethod
    def fromObj(cls, obj, activity):
        to = cls()
        d = obj["d"].split("/")
        to.year = long(d[2])
        to.month = long(d[1])
        to.day = long(d[0])
        d = datetime.date(to.year, to.month, to.day)
        to.epoch = get_epoch_from_datetime(d)
        to.activity = activity
        return to

@deserializer
def _ds_collection_to(stream, version):
    to = CollectionTO()
    to.epoch = ds_long(stream)
    to.year = ds_long(stream)
    to.month = ds_long(stream)
    to.day = ds_long(stream)
    _version = ds_long(stream)
    to.activity = _ds_activity_to(stream, _version)
    return to

@serializer
def _s_collection_to(stream, to):
    s_long(stream, to.epoch)
    s_long(stream, to.year)
    s_long(stream, to.month)
    s_long(stream, to.day)
    s_long(stream, CURRENT_ACTIVITY_VERSION)
    _s_activity_to(stream, to.activity)

def _s_collection_list(stream, l):
    s_long(stream, 1)
    f = get_list_serializer(_s_collection_to)
    f(stream, l)

def _ds_collection_list(stream):
    l = list()
    version = ds_long(stream)
    f = get_list_deserializer(_ds_collection_to, True)
    for to in f(stream, version):
        l.append(to)
    return l

register(List(CollectionTO), _s_collection_list, _ds_collection_list)
