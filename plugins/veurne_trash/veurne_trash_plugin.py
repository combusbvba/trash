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

from framework.plugin_loader import Plugin, get_plugin
from plugins.veurne_trash.admin import StatsHandler
from plugins.veurne_trash.cron import BroadcastNotificationsHandler
from plugins.veurne_trash.rogerthat_callbacks import system_api_call
from framework.utils.plugins import Handler
from plugins.rogerthat_api.rogerthat_api_plugin import RogerthatApiPlugin

class VeurneTrashPlugin(Plugin):

    def __init__(self, configuration):
        super(VeurneTrashPlugin, self).__init__(configuration)
        rogerthat_api_plugin = get_plugin('rogerthat_api')
        assert isinstance(rogerthat_api_plugin, RogerthatApiPlugin)
        rogerthat_api_plugin.subscribe('system.api_call', system_api_call)

    def get_handlers(self, auth):
        if auth == Handler.AUTH_ADMIN:
            yield Handler(url='/admin/cron/notifications/broadcast', handler=BroadcastNotificationsHandler)
            yield Handler(url='/admin/stats', handler=StatsHandler)
