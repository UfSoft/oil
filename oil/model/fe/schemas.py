# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: schemas.py 16 2007-08-30 00:16:26Z s0undt3ch $
# =============================================================================
#             $URL: http://oil.ufsoft.org/svn/trunk/oil/model/fe/schemas.py $
# $LastChangedDate: 2007-08-30 01:16:26 +0100 (Thu, 30 Aug 2007) $
#             $Rev: 16 $
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

#class AddBot(Schema):
#    allow_extra_fields = True
#    filter_extra_fields = True
##    nick = validators.UnicodeString(not_empty=True, encoding='UTF-8')
#    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
##    passwd = validators.UnicodeString(not_empty=True, encoding='UTF-8')
##    passwd_confirm = validators.UnicodeString(not_empty=True, encoding='UTF-8')
#    user_id = validators.Int(not_empty=True)

class RegisterBot(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = validator.UniqueBotName(not_empty=True, encoding='UTF-8')
    user_id = validators.Int(not_empty=True)

class UpdateBot(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    #bot_id = validators.Int(not_empty=True)
    user_id = validators.Int(not_empty=True)
#    allow_extra_fields = True
#    filter_extra_fields = True
#    nick = validators.UnicodeString(not_empty=True, encoding='UTF-8')
#    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
#    passwd = validators.UnicodeString(not_empty=False, encoding='UTF-8')
#    passwd_confirm = validators.UnicodeString(not_empty=False, encoding='UTF-8')
    #networks = validator.ValidNetworkAddrPortPair(not_empty=False, encoding='UTF-8')
#    user_id = validators.Int(not_empty=True)
#    chained_validators = [ validators.FieldsMatch('passwd', 'passwd_confirm') ]


class AddNetwork(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nick = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    address = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    port = validators.Int(not_empty=True)
    passwd = validators.UnicodeString(not_empty=False, encoding='UTF-8')
    passwd_confirm = validators.UnicodeString(not_empty=False, encoding='UTF-8')
    user_id = validators.Int(not_empty=True)
    chained_validators = [ validators.FieldsMatch('passwd', 'passwd_confirm') ]

class UpdateNetwork(Schema):
    nick = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    passwd = validators.UnicodeString(not_empty=False, encoding='UTF-8')
    passwd_confirm = validators.UnicodeString(not_empty=False, encoding='UTF-8')
    participation_id = validators.Int(not_empty=True)
    user_id = validators.Int(not_empty=True)
    clear_passwd = validators.Int(if_missing=0)
    submit = validators.Bool()

class AddChannel(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    channel = validator.ValidChannelName(not_empty=False, encoding='UTF-8')
    participation_id = validators.Int(not_empty=True)