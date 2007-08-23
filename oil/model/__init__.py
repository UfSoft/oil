from pylons import config
#from oil.lib.helpers import url_for
#from sqlalchemy import Column, MetaData, Table, types
import sqlalchemy as sqla
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
import datetime
from pytz import UTC

# Global session manager.
#S ession() returns the session object appropriate for the current web request.
Session = scoped_session(sessionmaker(autoflush=True,
                                      transactional=True,
                                      bind=config['pylons.g'].sa_engine))


# Global metadata.
# If you have multiple databases with overlapping table names, you'll need a
# metadata for each database.
metadata = sqla.MetaData()

users = sqla.Table('users', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('name', sqla.Unicode(60), nullable=False, unique=True),
    sqla.Column('openid', sqla.String),
    sqla.Column('slug', sqla.String),
    sqla.Column('signup', sqla.DateTime(timezone=True), nullable=False),
    sqla.Column('lastlogin', sqla.DateTime(timezone=True), nullable=False),
    sqla.Column('email', sqla.Unicode, nullable=True, unique=True),
    sqla.Column('banned', sqla.Boolean, nullable=False, default=False),
    sqla.Column('type', sqla.String(7), nullable=False, default="user"),
    sqla.Column('language', sqla.Unicode, nullable=True, default="en"),
    sqla.Column('tzinfo', sqla.Unicode, nullable=True, default="UTC"),

)

class User(object):
    def __init__(self, openid, name=None):
        self.openid = openid
        self.name = name if name is not None else openid
        self.signup = UTC.localize(datetime.datetime.utcnow())
        self.updatelastlogin()
    def __unicode__(self):
        return self.name
    def updatelastlogin(self):
        self.lastlogin = UTC.localize(datetime.datetime.utcnow())
    def is_admin(self):
        return self.type == 'admin'
    def is_manager(self):
        return self.type == 'manager'

mapper(User, users, order_by=[sqla.asc(users.c.name)])