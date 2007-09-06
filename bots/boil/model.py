#from pylons import config
#import sqlalchemy as sqla
#from sqlalchemy.orm import mapper, relation
#from sqlalchemy.orm import scoped_session, sessionmaker
#
### import oil models
##from oil.model import bots
##from sqlalchemy.ext.associationproxy import association_proxy
##import datetime
##from pytz import UTC
#
## Global session manager.
## Session() returns the session object appropriate for the current web request.
#Session = scoped_session(sessionmaker(autoflush=True,
#                                      transactional=True,
#                                      bind=config['pylons.g'].sa_engine))
#
## Global metadata.
## If you have multiple databases with overlapping table names, you'll need a
## metadata for each database.
#metadata = sqla.MetaData()
#
#active_bots = sqla.Table('active_bots', metadata,
#    sqla.Column('bot_id', sqla.Integer, nullable=False, unique=True, primary_key=True),
#    sqla.Column('status', sqla.Boolean)
#)

from oil.model import *

