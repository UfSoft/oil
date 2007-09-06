import os
import sys
from optparse import OptionParser
from pylons import config
from sqlalchemy import engine_from_config
from paste.deploy import loadapp

import logging

def main():
    parser = OptionParser(
        usage = "%prog [config_file]",
        version = "0.1",
        description = "bots network launcher"
    )
    parser.add_option('-c', '--config',
        dest = 'cfgfile',
        help = 'path to configuration file'
    )
    parser.add_option('-p', '--sqla-prefix',
        dest = 'sqlaprefix',
        default = 'sqlalchemy.',
        help = 'SQLAlchemy config prefix (default: %default)'
    )

    options, args = parser.parse_args()
    if not options.cfgfile and not args:
        parser.error("You need to pass the config file")
    elif not options.cfgfile and args:
        options.cfgfile = args[0]

    cfgfile = os.path.abspath(options.cfgfile)
    loadapp('config:%s' % os.path.abspath(cfgfile))
    config['pylons.g'].sa_engine = engine_from_config(config,
                                                      options.sqlaprefix)

    print 'setting up logging'
    from paste.script.util.logging_config import fileConfig
#    import logging.config
#    logging.config.fileConfig(open(cfgfile, 'r'))
    fileConfig(cfgfile)
    log = logging.getLogger(__name__)
    log.debug('foo......')
    log.error('bar!')

    import network, irclib
    bnw = network.IRCBotsNetwork()
    try:
        bnw.connect_all()
        bnw.process_all()
    except (KeyboardInterrupt, irclib.ServerNotConnectedError):
        bnw.quit()
    finally:
        sys.exit()



if __name__ == "__main__":
    main()