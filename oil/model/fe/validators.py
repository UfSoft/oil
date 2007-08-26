# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: validators.py 15 2007-08-26 16:31:24Z s0undt3ch $
# =============================================================================
#             $URL: http://oil.ufsoft.org/svn/trunk/oil/model/fe/validators.py $
# $LastChangedDate: 2007-08-26 17:31:24 +0100 (Sun, 26 Aug 2007) $
#             $Rev: 15 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

from formencode import validators, Invalid
from pylons.i18n import N_, _
from pylons import request, c
import oil.model as model
import logging

log = logging.getLogger(__name__)

class UniqueAddress(validators.UnicodeString):

    def validate_python(self, value, state):
        log.debug('validating python for unique address')
        #bot = model.Session.query(model.Bot).get(request.POST['bot_id'])
        query = model.Session.query(model.Network)
        query = query.filter(model.Network.bots.any(
            id=int(request.POST['bot_id']))
        )
        networks = query.filter_by(port=int(request.POST['port'])).all()
        log.debug(networks)
        for net in networks:
            log.debug(net)
            if net.address == value:
                raise Invalid(
                    _("There's already a network by this name for %s" % \
                      net.bot.name), value, state)


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