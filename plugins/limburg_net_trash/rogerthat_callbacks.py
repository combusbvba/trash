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

from plugins.limburg_net_trash.plugin_bizz import get_streets, get_street_numbers, set_location, set_notifications
from plugins.limburg_net_trash.plugin_utils import get_email_and_app_id_from_userdetails

def system_api_call(rt_settings, id_, email, method, params, tag, service_identity, user_details):
    email, app_id = get_email_and_app_id_from_userdetails(user_details)
    if method and method == u"trash.getStreets":
        return get_streets(rt_settings.sik, service_identity, email, app_id, params)
    elif method and method == u"trash.getStreetNumbers":
        return get_street_numbers(rt_settings.sik, service_identity, email, app_id, params)
    elif method and method == u"trash.setLocation":
        return set_location(rt_settings.sik, service_identity, email, app_id, params)
    elif method and method == u"trash.setNotifications":
        return set_notifications(rt_settings.sik, service_identity, email, app_id, params)
    return None
