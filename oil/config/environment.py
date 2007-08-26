"""Pylons environment configuration"""
import os

from pylons import config

import oil.lib.app_globals as app_globals
import oil.lib.helpers
from oil.config.routing import make_map
from sqlalchemy import engine_from_config
from pylons.i18n import ugettext
from genshi.filters import Translator

def template_loaded(template):
    #return template # while genshi bug #129 is not fixed :\
    template.filters.insert(0, Translator(ugettext))

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config`` object"""
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='oil',
                    template_engine='genshi', paths=paths)

    config['pylons.g'] = app_globals.Globals()
    config['pylons.h'] = oil.lib.helpers
    config['routes.map'] = make_map()

    # Customize templating options via this variable
    tmpl_options = config['buffet.template_options']
    tmpl_options['genshi.loader_callback'] = template_loaded

    # CONFIGURATION OPTIONS HERE (note: all config options will override any
    # Pylons config options)
    config['pylons.g'].sa_engine = engine_from_config(config, 'sqlalchemy.')
