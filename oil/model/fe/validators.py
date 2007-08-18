# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: validators.py 5 2007-08-18 16:05:25Z s0undt3ch $
# =============================================================================
#             $URL: http://oil.ufsoft.org/svn/trunk/oil/model/fe/validators.py $
# $LastChangedDate: 2007-08-18 17:05:25 +0100 (Sat, 18 Aug 2007) $
#             $Rev: 5 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

from formencode import validators, Invalid
from pylons.i18n import N_, _
from pylons import request
import irclv.model as model

class UniqueAddress(validators.UnicodeString):
    def validate_python(self, value, state):
        del model.sac.session_context.current
        network = model.sac.query(model.Network).get_by(address=value)
        if network:
            raise Invalid(_("Address is already used for network '%s'") % \
                          network.name, value, state)

class UniqueChannel(validators.UnicodeString):
    def validate_python(self, value, state):
        del model.sac.session_context.current
        network = request.POST['network']
        channel = model.sac.query(model.Network).get_by(address=value)
        if network:
            raise Invalid(_("Address is already used for network '%s'") % \
                          network.name, value, state)
