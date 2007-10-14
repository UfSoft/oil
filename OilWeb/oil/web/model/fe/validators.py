# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: validators.py 33 2007-10-14 15:08:27Z s0undt3ch $
# =============================================================================
#             $URL: http://oil.ufsoft.org/svn/trunk/OilWeb/oil/web/model/fe/validators.py $
# $LastChangedDate: 2007-10-14 16:08:27 +0100 (Sun, 14 Oct 2007) $
#             $Rev: 33 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

from formencode import validators, Invalid
from pylons.i18n import N_, _
from pylons import request, c
import oil.db as model
import logging

log = logging.getLogger(__name__)

class UniqueBotName(validators.UnicodeString):
    def validate_python(self, value, state):
        log.debug(repr(value))
        bot = model.Session.query(model.Bot).filter_by(name=value).first()
        if bot:
            raise Invalid(_('A bot with that name already exists. '
                            'Please choose another name.'), value, state)

class ChannelList(validators.FancyValidator):
    def _to_python(self, value, state):
        log.debug('channel list to_python')
        log.debug([channel.strip(',#').lower() for channel in value.split()])
        return [channel.strip(',#') for channel in value.split()]

    def validate_python(self, value, state):
        log.debug('validating python')
        log.debug(value)
        _channels = []
        for channel in value:
            if channel.lower() in _channels:
                value = filter(None, value)
                raise Invalid(
                    _("No need to duplicate channel names: '%s'." % \
                      u', '.join(val for val in value)), value, state)
            _channels.append(channel.lower())

    def _from_python(self, value, state):
        log.debug('channel list from_python')
        log.debug(u' '.join([u'#%s' for channel in value]))
        return u' '.join([u'#%s' for channel in value])

class ValidChannelName(validators.UnicodeString):
    def _to_python(self, value, state):
        return value.strip('#').lower()
