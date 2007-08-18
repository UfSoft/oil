# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: validators.py 6 2007-08-18 17:04:07Z s0undt3ch $
# =============================================================================
#             $URL: http://oil.ufsoft.org/svn/trunk/oil/model/fe/validators.py $
# $LastChangedDate: 2007-08-18 18:04:07 +0100 (Sat, 18 Aug 2007) $
#             $Rev: 6 $
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

