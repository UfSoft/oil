# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: schemas.py 33 2007-10-14 15:08:27Z s0undt3ch $
# =============================================================================
#             $URL: http://oil.ufsoft.org/svn/trunk/OilWeb/oil/web/model/fe/schemas.py $
# $LastChangedDate: 2007-10-14 16:08:27 +0100 (Sun, 14 Oct 2007) $
#             $Rev: 33 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================
from formencode import Schema, validators
from oil.web.model.fe import validators as validator

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
    #allow_extra_fields = True
    #filter_extra_fields = True
    name = validator.UniqueBotName(not_empty=True, encoding='UTF-8')
    user_id = validators.Int(not_empty=True)

class UpdateBot(Schema):
    #allow_extra_fields = True
    #filter_extra_fields = True
    name = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    bot_id = validators.Int(not_empty=True)
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
    #allow_extra_fields = True
    #filter_extra_fields = True
    nick = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    address = validators.UnicodeString(not_empty=True, encoding='UTF-8')
    port = validators.Int(not_empty=True)
    passwd = validators.UnicodeString(not_empty=False, encoding='UTF-8')
    passwd_confirm = validators.UnicodeString(not_empty=False, encoding='UTF-8')
    user_id = validators.Int(not_empty=True)
    bot_id = validators.Int(not_empty=True)
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
    prefix = validator.ValidChannelName(not_empty=False, encoding='UTF-8')
    participation_id = validators.Int(not_empty=True)
