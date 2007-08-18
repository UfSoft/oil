# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: schemas.py 6 2007-08-18 17:04:07Z s0undt3ch $
# =============================================================================
#             $URL: http://oil.ufsoft.org/svn/trunk/oil/model/fe/schemas.py $
# $LastChangedDate: 2007-08-18 18:04:07 +0100 (Sat, 18 Aug 2007) $
#             $Rev: 6 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================
from formencode import Schema, validators
from oil.model.fe import validators as validator

class AddNetwork(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    address = validator.UniqueAddress(not_empty=True, encoding='UTF-8')
    port = validators.Int(not_empty=True)


