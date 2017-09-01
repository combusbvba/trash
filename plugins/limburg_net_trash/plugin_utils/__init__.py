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
import time

from mcfw.properties import azzert
from framework.utils import now


def get_email_and_app_id_from_userdetails(user_details):
    return user_details[0]["email"], user_details[0]["app_id"]

def today():
    n = now()
    return n - n % 86400

# @returns(int)
# @arguments((datetime.datetime, datetime.date))
def get_epoch_from_datetime(datetime_):
    if isinstance(datetime_, datetime.datetime):
        epoch = datetime.datetime.utcfromtimestamp(0)
    elif isinstance(datetime_, datetime.date):
        epoch = datetime.date.fromtimestamp(0)
    else:
        azzert(False, "Provided value should be a datetime.datetime or datetime.date instance")
    delta = datetime_ - epoch
    return int(delta.total_seconds())

def get_current_queue():
    try:
        import webapp2
        request = webapp2.get_request()
        if request:
            return request.headers.get('X-Appengine-Queuename', None)
    except:
        logging.warn('Failed to get the name of the current queue', exc_info=1)
