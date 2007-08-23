"""The application's Globals object"""
from pylons import config
from paste.deploy.converters import asbool
from openid.store.filestore import FileOpenIDStore

class Globals(object):
    """Globals acts as a container for objects available throughout the life of
    the application.
    """

    def __init__(self):
        """One instance of Globals is created during application initialization
        and is available during requests via the 'g' variable.
        """
        openid_store_dir = config['app_conf']['openid.store.dir']
        self.openid_store = FileOpenIDStore(openid_store_dir)
        if asbool(config['app_conf']['openid.development.mode']):
            self.development_mode = True
        else:
            self.development_mode = False
        pass
