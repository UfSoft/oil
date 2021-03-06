"""The base Controller API

This module provides the BaseController for all controllers to subclass, as
well as functions and objects for use by those controllers.
"""
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, validate
from pylons.i18n import _, ungettext, N_
from pylons.templating import render

import oil.bots.helpers as h
from oil import db as model

class BaseController(WSGIController):

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method the
        # request is routed to. This routing information is available in
        # environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            #log.debug("removing db session")
            model.Session.remove()

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
