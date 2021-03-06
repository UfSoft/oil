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
    map.connect('edit_network', 'networks/edit/:nick/:network',
                controller='networks', action='edit', nick=None, network=None)
    map.connect('delete_channel', 'channels/delete/:id/:channel',
                controller='channels', action='delete',
                id=None, channel=None)
    map.connect('logs', 'logs/:network/:channel/:year/:month/:day',
                controller='logs', action='view', network=None, channel=None,
                year=None, month=None, day=None)

    map.connect('add_channels', 'channels/:action/:nick/:network',
                controller='channels')

    map.connect('feed_logs', 'feed/:network/:channel',
                controller='feed', action='logs', network=None, channel=None)

    map.connect(':controller/:action/:id', id=None, bot=None, network=None,
                channel=None, nick=None, year=None, month=None, day=None)
    map.connect('*url', controller='template', action='view')

    return map
