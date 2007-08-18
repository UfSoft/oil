from pylons import config
#from sqlalchemy import Column, MetaData, Table, types
import sqlalchemy as sqla
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
import datetime
from pytz import UTC

# Global session manager.
#Session() returns the session object appropriate for the current web request.
Session = scoped_session(sessionmaker(autoflush=True,
                                      transactional=True,
                                      bind=config['pylons.g'].sa_engine))


# Global metadata.
# If you have multiple databases with overlapping table names, you'll need a
# metadata for each database.
metadata = sqla.MetaData()

class UTCDateTime(sqla.types.TypeDecorator):
    impl = sqla.types.DateTime
    def convert_bind_param(self, value, engine):
        return value
    def convert_result_value(self, value, engine):
        return UTC.localize(value)

user_table = sqla.Table('user', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('name', sqla.Unicode(60), nullable=False, unique=True),
    sqla.Column('openid', sqla.String()),
    sqla.Column('signup', UTCDateTime, nullable=False),
    sqla.Column('lastlogin', UTCDateTime, nullable=False),
    sqla.Column('banned', sqla.Boolean, nullable=False, default=False),
    sqla.Column('type', sqla.String(6), nullable=False, default="user"),
    sqla.Column('tzinfo', sqla.Unicode, nullable=True, default="UTC"),

)

class User(object):
    def __init__(self, openid, name=None):
        self.openid = openid
        self.name = name if name is not None else openid
        self.signup = datetime.datetime.utcnow()
    def __unicode__(self):
        return self.name
    def updatelastlogin(self):
        self.lastlogin = datetime.datetime.utcnow()
    def is_admin(self):
        return isinstance(self, Admin)

class Manager(User):
    pass

class Admin(Manager):
    pass

mapper(User, user_table, order_by=[sqla.asc(user_table.c.name)])
mapper(Manager, user_table, order_by=[sqla.asc(user_table.c.name)])
mapper(Admin, user_table, order_by=[sqla.asc(user_table.c.name)])

network_table = sqla.Table('network', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('name', sqla.Unicode, nullable=False, unique=True),
    sqla.Column('address', sqla.Unicode, nullable=False, unique=True),
    sqla.Column('port', sqla.Integer, nullable=False, unique=False),
    sqla.Column('added', UTCDateTime, nullable=False, unique=False),
    sqla.Column('manager_id', sqla.Integer, sqla.ForeignKey('user.id'))
)

class Network(object):
    def __init__(self, address, port, name=None):
        self.address = address
        self.port = port
        self.added = datetime.datetime.utcnow()
        if name is None:
            self.name = self.address
        else:
            self.name = name
    def __unicode__(self):
        return '%s:%d' % (self.address, self.port)
    def __repr__(self):
        return '<%s: %s:%d>' % (self.name, self.address, self.port)
    def has_channel(self, channel):
        return channel in [channel.name for channel in self.channels]

channel_table = sqla.Table('channel', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('network_id', sqla.Integer, sqla.ForeignKey('network.id')),
    sqla.Column('name', sqla.Unicode, nullable=False, unique=True),
    sqla.Column('topic', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('first_entry', sqla.Date, nullable=True, unique=False),
    sqla.Column('last_entry', sqla.Date, nullable=True, unique=False),
)

class Channel(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        #network = sac(Network).get_by(id=network_id)
        return '<%s: %s>' % (self.name,
                             Session.query(Network).get_by(id=self.network_id).name)
    def __unicode__(self):
        return self.name

    def add_event(self, type, source, message):
        event = Event(type, source, message)
        self.events.append(event)
        self.update_last_entry_date(event.stamp)


    def update_last_entry_date(self, date):
        if not self.first_entry:
            self.first_entry = date
        self.last_entry = date

event_table = sqla.Table('event', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('channel_id', sqla.Integer, sqla.ForeignKey('channel.id')),
    sqla.Column('stamp', UTCDateTime, nullable=False, unique=False),
    sqla.Column('type', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('subtype', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('source', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('msg', sqla.Unicode, nullable=False, unique=False),
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
        return '<%s: (%s %s) %r>' % (self.type, self.stamp, self.msg)


mapper(Network, network_table,
       properties = {'channels': relation(Channel)},
       order_by=[sqla.asc(network_table.c.name)])

mapper(Channel, channel_table,
       properties = {'events': relation(Event)},
       order_by=[sqla.asc(channel_table.c.name)])

mapper(Event, event_table, order_by=[sqla.asc(event_table.c.stamp)])