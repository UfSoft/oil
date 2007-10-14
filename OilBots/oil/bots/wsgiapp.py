"""The BOil WSGI application"""
import os

from paste.cascade import Cascade
from paste.registry import RegistryManager
from paste.urlparser import StaticURLParser
from paste.deploy.converters import asbool
from pylons import config
from pylons.error import error_template
from pylons.middleware import error_mapper, ErrorDocuments, ErrorHandler, \
    StaticJavascripts
from pylons.wsgiapp import PylonsApp

import oil.bots.helpers
from oil.bots.routing import make_map

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config`` object"""
    # Pylons paths
    root = os.path.dirname(os.path.abspath(__file__))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='oil.bots',
                    template_engine='genshi', paths=paths)

    config['pylons.g'] = Globals()
    config['pylons.h'] = oil.bots.helpers
    config['routes.map'] = make_map()

    # Customize templating options via this variable
    tmpl_options = config['buffet.template_options']

    # CONFIGURATION OPTIONS HERE (note: all config options will override any
    # Pylons config options)


def make_app(global_conf, full_stack=True, **app_conf):
    """Create a Pylons WSGI application and return it

    ``global_conf``
        The inherited configuration for this application. Normally from the
        [DEFAULT] section of the Paste ini file.

    ``full_stack``
        Whether or not this application provides a full WSGI stack (by default,
        meaning it handles its own exceptions and errors). Disable full_stack
        when this application is "managed" by another WSGI middleware.

    ``app_conf``
        The application's local configuration. Normally specified in the
        [app:<name>] section of the Paste ini file (where <name> defaults to
        main).
    """
    # Configure the Pylons environment
    load_environment(global_conf, app_conf)

    # The Pylons WSGI app
    app = PylonsApp()

    # CUSTOM MIDDLEWARE HERE (filtered by the error handling middlewares)
    if asbool(full_stack):
        # Handle Python exceptions
        app = ErrorHandler(app, global_conf, error_template=error_template,
                           **config['pylons.errorware'])

        # Display error documents for 401, 403, 404 status codes (and 500 when
        # debug is disabled)
        app = ErrorDocuments(app, global_conf, mapper=error_mapper, **app_conf)

    # Establish the Registry for this application
    app = RegistryManager(app)

    # Static files
    javascripts_app = StaticJavascripts()
    static_app = StaticURLParser(config['pylons.paths']['static_files'])
    app = Cascade([static_app, javascripts_app, app])


    try:
        import threading
        from oil.bots.IRC import network
        #from oil.lib.helpers import url_for
        irc = network.IRCBotsNetwork(app_conf['base_url'])
    #    irc.setDaemon(True)
    #    irc.start()
        irc.connect_all()
    #    irc.process_all()
    #    irc.register()
    ##    th1 = threading.Timer(0.5, irc.connect_all)
    ##    th1.setDaemon(True)
    ##    th1.start()
        th2 = threading.Timer(2.0, irc.process_all)
    #    th2 = threading.Thread(target=irc.process_all)
    #    th2.setDaemon(True)
        th2.start()
    ##    th = threading.Thread(target=irc.process_all)
    ##    th2.start()
    ##    th3 = threading.Timer(50.0, irc.register)
    ##    th3.setDaemon(True)
    #    th3.start()
    except (SystemExit, KeyboardInterrupt), e:
        print e
        irc.quit()
    config['pylons.g'].ircnw = irc
    print config['pylons.g'].ircnw

    return app



from sqlalchemy import engine_from_config

class Globals(object):
    """Globals acts as a container for objects available throughout the life of
    the application.
    """

    def __init__(self):
        """One instance of Globals is created during application initialization
        and is available during requests via the 'g' variable.
        """
        self.sa_engine = engine_from_config(config, 'sqlalchemy.')
