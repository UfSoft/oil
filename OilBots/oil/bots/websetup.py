"""Setup the OIL application"""
import logging

from paste.deploy import appconfig
from pylons import config

from oil.bots.wsgiapp import load_environment

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup oil here"""
    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf)
    # Forced late import of model
    from oil import db as model
    answer = raw_input('Delete Current Tables If any exist [y/n]?')
    if answer.lower() in ('y', 'yes', ''):
        model.metadata.drop_all(bind=config['pylons.g'].sa_engine)
        log.info('Tables Deleted')
    log.info("Creating tables")
    model.metadata.create_all(bind=config['pylons.g'].sa_engine,
                              checkfirst=True)
    log.info("Tables Created")
