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

bots = sqla.Table('bots', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('nick', sqla.Unicode, nullable=False, unique=True),
    sqla.Column('name', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('passwd', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('user_id', sqla.Integer, sqla.ForeignKey('users.id')),
    sqla.Column('network_id', sqla.Integer, sqla.ForeignKey('networks.id'))
)

class Bot(object):
    def __init__(self, nick, name=None, passwd=None):
        self.nick = nick
        self.name = name
        self.passwd = passwd

    def __unicode__(self):
        return self.nick

    def __repr__(self):
        return '<%r: Owned by %r>' % (
            self.name,
            Session.query(User).filter_by(id=self.user_id).first().name
        )

networks = sqla.Table('networks', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('address', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('port', sqla.Integer, nullable=False, unique=False),
)
sqla.Index('networks_idx', networks.c.address, networks.c.port, unique=True)

class Network(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
    def __unicode__(self):
        return '%s:%d' % (self.address, self.port)
    def __repr__(self):
        return '<IRC Network: %s:%d>' % (self.address, self.port)

channels = sqla.Table('channels', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('name', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('topic', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('first_entry', sqla.Date, nullable=True, unique=False),
    sqla.Column('last_entry', sqla.Date, nullable=True, unique=False),
    sqla.Column('network_id', sqla.Integer, sqla.ForeignKey('networks.id'))
)
sqla.Index('channels_idx', channels.c.name, channels.c.network_id, unique=True)

class Channel(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        network = Session.Query(Network).filter_by(id=self.network_id).first()
        return '<IRC Channel: %s on %s:%d>' % (
            self.name, network.address, network.port
        )

    def __unicode__(self):
        return self.name

#    def add_event(self, type, source, message):
#        event = Event(type, source, message)
#        self.events.append(event)
#        self.update_last_entry_date(event.stamp)


    def update_last_entry_date(self, date):
        if not self.first_entry:
            self.first_entry = date
        self.last_entry = date


events = sqla.Table('events', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('stamp', sqla.DateTime(timezone=True), nullable=False, unique=False),
    sqla.Column('type', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('subtype', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('source', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('msg', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('channel_id', sqla.Integer, sqla.ForeignKey('channels.id')),
)

class Event(object):
    def __init__(self, type, source, message):
        self.source = source
        self.msg = message
        self.type = type
        self.stamp = datetime.datetime.utcnow()
    def __unicode__(self):
        return self.msg
    def __repr__(self):
        return '<IRC Event: %s %r %r>' % (self.stamp, self.type, self.msg)

mapper(Network, networks, order_by=[sqla.asc(networks.c.address),
                                    sqla.asc(networks.c.port)],
        properties={
            'channels': relation(Channel,
                                 backref=sqla.orm.backref('network',
                                                          uselist=False))
        }
)

mapper(Channel, channels, order_by=[sqla.asc(channels.c.name)],
       properties={'network': relation(Network, backref='channels')}
)


mapper(Bot, bots, order_by=[sqla.asc(bots.c.nick)],
       properties={
            'owner': relation(User, backref='bots'),
            'networks': relation(Network, backref='bots')
        }
)
