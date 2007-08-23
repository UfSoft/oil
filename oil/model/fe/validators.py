# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: validators.py 12 2007-08-23 22:16:30Z s0undt3ch $
# =============================================================================
#             $URL: http://oil.ufsoft.org/svn/trunk/oil/model/fe/validators.py $
# $LastChangedDate: 2007-08-23 23:16:30 +0100 (Thu, 23 Aug 2007) $
#             $Rev: 12 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

from formencode import validators, Invalid
from pylons.i18n import N_, _
from pylons import request
import oil.model as model

class UniqueAddress(validators.UnicodeString):
    def validate_python(self, value, state):
        query = model.Session.query(model.Network)
        network = query.filter_by(address=value).first()
        if network:
            raise Invalid(_("Address is already used for network '%s'") % \
                          network.name, value, state)
        model.Session.remove()

class ValidNetworkAddrPortPair(validators.FancyValidator):

    def to_python(self, value, state):
        networks = []
        for entry in [tuple(value.strip(',').split(':')) for value in value.split()]:
            if len(entry) == 3:
                name, address, port = entry
            else:
                address, port = entry
                name = u'%s-%s' % (address, port)
            networks.append((name, address, port))
        return networks

    def validate_python(self, value, state):
        for item in value:
            if not len(item)==3:
                raise Invalid(_('Invalid network format for %r, should '
                              'be "name:address:port".') % item, value, state)

    def from_python(self, value, state):
        return u', '.join(u'%s:%s:%s' % (name, addr, port) for name, addr, port in value)

class ChannelList(validators.FancyValidator):
    def to_python(self, value, state):
        return [channel.strip(',#') for channel in value.split()]

    def from_python(self, value, state):
        return u', '.join([u'#%s' for channel in value])

    def validate_python(self, value, state):
        print 1111111, value

