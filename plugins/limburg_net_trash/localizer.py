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

import logging


DEFAULT_LANGUAGE = u"nl"

translations = \
{
u'nl': {
        u'collection_broadcast': u'Morgen (%(date)s) zijn er volgende ophalingen\n-%(collections)s',
        }
}


def translate_key(language, key, suppress_warning=False, _duplicate_backslashes=False, **kwargs):
    if not language:
        language = DEFAULT_LANGUAGE
    if not key:
        raise ValueError("key is a required argument")
    language = language.replace('-', '_')
    if not language in translations:
        if '_' in language:
            language = language.split('_')[0]
            if not language in translations:
                language = DEFAULT_LANGUAGE
        else:
            language = DEFAULT_LANGUAGE
    if key in translations[language]:
        s = translations[language][key]
    else:
        if key not in translations[DEFAULT_LANGUAGE]:
            raise ValueError("Translation key '%s' not found for default language" % (key))
        if not suppress_warning:
            logging.warn("Translation key '%s' not found for language '%s' - fallback to default" % (key, language))
        s = translations[DEFAULT_LANGUAGE][key]

    if kwargs:
        s = s % kwargs

    if _duplicate_backslashes:
        s = s.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t').replace("'", "\\'").replace('"', '\\"')
    return s
