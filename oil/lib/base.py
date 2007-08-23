"""The base Controller API

Provides the BaseController class for subclassing, as well as functions and
objects for use by Controllers.
"""
import logging
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import rest, jsonify
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _, ungettext, N_
from pylons.templating import render

import oil.lib.helpers as h
import oil.model as model
from oil.lib.helpers import validate

import os
from babel import Locale
from babel.dates import get_timezone_name
from pytz import timezone, common_timezones

log = logging.getLogger(__name__)

class BaseController(WSGIController):

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method the
        # request is routed to. This routing information is available in
        # environ['pylons.routes_dict']
        c.user = model.Session.query(model.User).filter_by(openid=(session['openid'])).first() \
            if 'openid' in session and session['openid'] else None
        c.timezone = timezone(str(c.user.tzinfo) if c.user else 'UTC')

        log.debug(request.POST)
        if 'language' in request.POST.keys():
            language = request.POST['language']
            if h.get_lang() != language:
                h.set_lang(language)
                session['language'] = language
                session.save()
        elif 'language' in session.keys():
            current_lang = h.get_lang()
            if current_lang:
                #print current_lang
                if session['language'] != current_lang[0]:
                    h.set_lang(session['language'])
            else:
                h.set_lang(session['language'])
            language = session['language']
        else:
            language = 'en'
            h.set_lang(language)
            session['language'] = language
            session.save()

        g.locale, c.languages = self._set_language_dropdown_values(language)
        c.tz_list = self._build_timezones(g.locale)

        #session['message'] = 'FOOOO Barrrr FOOOO Barrrr FOOOO Barrrr FOOOO Barrrr FOOOO Barrrr '

        if 'message' in session and session['message'] != '':
            c.message = session['message']
            session['message'] = ''
            session.save()
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            model.Session.remove()

    @beaker_cache(type='memory')
    def _find_available_locales(self):
        available_locales = []
        i18ndir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               'i18n')
        for entry in os.listdir(i18ndir):
            mo_path = os.path.join(i18ndir, entry, 'LC_MESSAGES',
                                   'oil.mo')
            if os.path.isfile(mo_path):
                if '_' in entry:
                    available_locales.append(tuple(entry.split('_')))
                else:
                    available_locales.append((entry, None))
        return available_locales

    @beaker_cache(type='memory', key='initial_locale')
    def _set_language_dropdown_values(self, initial_locale=None):
        log.debug('Setting languages dropdown menu for %r' % initial_locale)
        available_locales = self._find_available_locales()
        locale = Locale.parse(initial_locale)
        languages = []
        current_lang = h.get_lang()[0]
        for loc, territory in available_locales:
            selected = False
            language = locale.languages[loc].capitalize()
            if territory:
                country = u'(%s)' % locale.territories[territory]
                value = ['%s_%s' % (loc, territory),
                         u'%s %s' % (language, country)]
                #if value[0] == (c.user.language if c.user else current_lang):
                if value[0] == current_lang:
                    selected = True
            else:
                value = [loc, language]
                #if value[0] == (c.user.language if c.user else current_lang):
                if value[0] == current_lang:
                    selected = True
            languages.append( value + [selected])
#        g.locale = locale
#        c.tz_list = self._build_timezones(locale)
        return locale, languages

    @beaker_cache(type='memory', key='locale')
    def _build_timezones(self, locale=None):
#        if 'tz.%s'%locale in cache:
#            log.debug('Returning cached timezones mapping for %s' % locale)
#            return cache['tz.%s'%locale]
        log.debug('UPDATING TZs for %r', h.get_lang()[0])
        tz_list = []
        #longest = max([len(tz) for tz in common_timezones])
        #format = "%%-%ds %%s" % max(8, longest + 1)
        for tzname in common_timezones:
            try:
                tz = {}
                tz['value'] = tzname
                tz['name'] = get_timezone_name(timezone(tzname), locale=locale)
                tz_list.append(tz)
                #log.debug(tz)
            except KeyError:
                pass
        tz_list.sort(lambda x,y: cmp(x['value'], y['value']))
#        cache['tz.%s'%locale] = tz_list
        return tz_list
        #c.tz_list = tz_list


# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
