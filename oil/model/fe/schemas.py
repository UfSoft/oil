# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: schemas.py 12 2007-08-23 22:16:30Z s0undt3ch $
# =============================================================================
#             $URL: http://oil.ufsoft.org/svn/trunk/oil/model/fe/schemas.py $
# $LastChangedDate: 2007-08-23 23:16:30 +0100 (Thu, 23 Aug 2007) $
#             $Rev: 12 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================
from formencode import Schema, validators
from oil.model.fe import validators as validator

class UpdateUser(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    openid = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    email = validators.Email(resolve_domain=True, not_empty=False)

class AddNetwork(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    address = validator.UniqueAddress(not_empty=True, encoding='UTF-8')
    port = validators.Int(not_empty=True)

class AddBot(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nick = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    passwd = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    passwd_confirm = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    user_id = validators.Int(not_empty=True)

class RegisterBot(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nick = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    passwd = validators.UnicodeString(not_empty=False, encoding='UTF-8')
    passwd_confirm = validators.UnicodeString(not_empty=False, encoding='UTF-8')
    user_id = validators.Int(not_empty=True)
    chained_validators = [ validators.FieldsMatch('passwd', 'passwd_confirm') ]

class AddNetwork(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    address = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    port = validators.Int(not_empty=True)
#class UpdateBot(Schema):
class UpdateBot(RegisterBot):
    pass
#    allow_extra_fields = True
#    filter_extra_fields = True
#    nick = validators.UnicodeString(not_empty=True, encoding='UTF-8')
#    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
#    passwd = validators.UnicodeString(not_empty=False, encoding='UTF-8')
#    passwd_confirm = validators.UnicodeString(not_empty=False, encoding='UTF-8')
    #networks = validator.ValidNetworkAddrPortPair(not_empty=False, encoding='UTF-8')
#    user_id = validators.Int(not_empty=True)
#    chained_validators = [ validators.FieldsMatch('passwd', 'passwd_confirm') ]

class UpdateChannels(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    channels = validator.ChannelList(not_empty=False, encoding='UTF-8')

