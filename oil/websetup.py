"""Setup the OIL application"""
import logging

from paste.deploy import appconfig
from pylons import config

from oil.config.environment import load_environment

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup oil here"""
    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf)
    # Forced late import of model
    from oil import model
    answer = raw_input('Delete Current Tables If any exist [y/n]?')
    if answer.lower() in ('y', 'yes', ''):
        model.metadata.drop_all(bind=config['pylons.g'].sa_engine)
        log.info('Tables Deleted')
    log.info("Creating tables")
    model.metadata.create_all(bind=config['pylons.g'].sa_engine,
                              checkfirst=True)
    log.info("Tables Created")
    #openid = raw_input("Please write your OpenID url (for administration): ")
    openid = 'http://pedro.algarvio.myopenid.com/'
    #query = model.Session.query(model.Admin)
    admin = model.User(openid)
    admin.updatelastlogin()
    admin.type = 'admin'
    model.Session.save(admin)
#    if config['openid.development.mode']:
#        import pwd, os
#        openid1 = pwd.getpwuid(os.getuid())[0]
#        log.info('In development mode, addign extra local admin %r' % openid1)
#        #query = model.Session.query(model.Admin)
#        admin1 = model.User(openid1)
#        admin1.updatelastlogin()
#        admin1.type = 'admin'
#        model.Session.save(admin1)
    model.Session.commit()
    log.info("Successfully setup admin's OpenID")
#    answer = raw_input('Add some networks to the database [y/n]?')
#    if answer.lower() in ('y', 'yes', ''):
#        #query = model.Session.query(model.Network)
#        log.info('  irc.freenode.net:6667')
#        network = model.Network('irc.freenode.net', 6667)
#        network.name = 'FreeNode'
#        #network.manager_id = admin.id
#        #channel = model.Channel('ufs')
#        #model.Session.save(channel)
#        #network.channels = [channel]
#        model.Session.save(network)
#        model.Session.commit()
#        log.info('  irc.oftc.net:6667')
#        network1 = model.Network('irc.oftc.net', 6667)
#        #network1.manager_id = admin.id
#        model.Session.save(network1)
#        model.Session.commit()
#        log.info('  irc.undernet.net:6667')
#        network2 = model.Network('irc.undernet.org', 6667)
#        #network2.manager_id = admin.id
#        model.Session.save(network2)
#        model.Session.commit()
    model.Session.commit()
    log.info('All Done!')
