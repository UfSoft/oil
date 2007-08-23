"""Routes configuration

The more specific and detailed routes should be defined first so they may take
precedent over the more generic routes. For more information refer to the
routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])

    # The ErrorController route (handles 404/500 error pages); it should likely
    # stay at the top, ensuring it can always be resolved
    map.connect('error/:action/:id', controller='error')

    # CUSTOM ROUTES HERE
    map.connect('home', '', controller="main", action="index")
    map.connect('view_networks', 'logs/', controller='logs',
                action='view_networks')
    map.connect('view_network', 'networks/:network/', controller='logs',
                action='view_network')
    map.connect('logs', 'logs/:network/:channel/:year/:month/:day',
                controller='logs', action='view', network=None, channel=None,
                year=None, month=None, day=None)
    map.connect('channels', 'edit/channels/:bot/:network',
                controller="account", action="edit_channels")
    map.connect('add_network', 'add/network/:bot',
                controller='account', action='add_network', bot=None)
    map.connect('edit_network', 'edit/network/:bot/:network',
                controller='account', action='edit_network', bot=None, network=None)

    # Default and Fallback routes
    map.connect(':controller/:action/:id', network=None, channel=None,
                year=None, month=None, day=None, bot=None)
    map.connect('*url', controller='template', action='view')

    return map
