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

class UTCDateTime(sqla.types.TypeDecorator):
    impl = sqla.types.DateTime
    def convert_bind_param(self, value, engine):
        return value
        #return UTC.localize(value)
    def convert_result_value(self, value, engine):
        return UTC.localize(value)

users = sqla.Table('users', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('name', sqla.Unicode(60), nullable=False, unique=True),
    sqla.Column('openid', sqla.String),
    sqla.Column('slug', sqla.String),
    sqla.Column('signup', UTCDateTime, nullable=False),
    sqla.Column('lastlogin', UTCDateTime, nullable=False),
    sqla.Column('email', sqla.Unicode, nullable=True, unique=True),
    sqla.Column('banned', sqla.Boolean, nullable=False, default=False),
    sqla.Column('type', sqla.String(7), nullable=False, default="user"),
    sqla.Column('language', sqla.Unicode, nullable=True, default="en"),
    sqla.Column('tzinfo', sqla.Unicode, nullable=True, default="UTC"),

)

user_association = sqla.Table('user_association', metadata,
    sqla.Column('bot_id', sqla.Integer, sqla.ForeignKey('bots.id')),
    sqla.Column('user_id', sqla.Integer, sqla.ForeignKey('users.id'))
)

#manager_table = sqla.Table('manager', metadata,
#    sqla.Column('id', sqla.Integer, sqla.ForeignKey('user.id'), primary_key=True)
#)
#
#admin_table = sqla.Table('admin', metadata,
#    sqla.Column('id', sqla.Integer, sqla.ForeignKey('user.id'), primary_key=True)
#)

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

#class Manager(User):
#    def __init__(self, openid, name=None):
#        User.__init__(self, openid, name)
#        self.type = 'manager'
#
#class Admin(Manager):
#    def __init__(self, openid, name=None):
#        Manager.__init__(self, openid, name)
#        self.type = 'admin'

networks = sqla.Table('networks', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('name', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('address', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('port', sqla.Integer, nullable=False, unique=False),
    sqla.Column('added', UTCDateTime, nullable=False, unique=False),
    sqla.Column('modified', UTCDateTime, nullable=False, unique=False),
)
sqla.Index('network', networks.c.name, networks.c.address, networks.c.port,
           unique=True)

network_association = sqla.Table('network_association', metadata,
    sqla.Column('bot_id', sqla.Integer, sqla.ForeignKey('bots.id')),
    sqla.Column('network_id', sqla.Integer, sqla.ForeignKey('networks.id'))
)

network_modifiers = sqla.Table('network_modifiers', metadata,
    sqla.Column('user_id', sqla.Integer, sqla.ForeignKey('users.id')),
    sqla.Column('network_id', sqla.Integer, sqla.ForeignKey('networks.id'))
)

class Network(object):
    def __init__(self, address, port, name=None):
        self.address = address
        self.port = port
        self.added = UTC.localize(datetime.datetime.utcnow())
        self.modified = UTC.localize(datetime.datetime.utcnow())
        if name is None:
            self.name = u'%s-%s' % (self.address, self.port)
        else:
            self.name = name
    def __unicode__(self):
        return '%s:%d' % (self.address, self.port)
    def __repr__(self):
        return '<%s: %s:%d>' % (self.name, self.address, self.port)
    def has_channel(self, channel):
        return channel in [channel.name for channel in self.channels]
    #def get_channel

channels = sqla.Table('channels', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('network_id', sqla.Integer, sqla.ForeignKey('networks.id')),
#    sqla.Column('bot_id', sqla.Integer, sqla.ForeignKey('bot.id')),
    sqla.Column('name', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('topic', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('first_entry', sqla.Date, nullable=True, unique=False),
    sqla.Column('last_entry', sqla.Date, nullable=True, unique=False),
)
sqla.Index('channel', channels.c.name, channels.c.network_id, unique=True)
channel_association = sqla.Table('channel_association', metadata,
    sqla.Column('bot_id', sqla.Integer, sqla.ForeignKey('bots.id')),
    sqla.Column('network_id', sqla.Integer, sqla.ForeignKey('networks.id')),
    sqla.Column('channel_id', sqla.Integer, sqla.ForeignKey('channels.id'))
)
sqla.Index('channel_assoc',
           channel_association.c.bot_id,
           channel_association.c.network_id,
           channel_association.c.channel_id,
           unique=True)

class Channel(object):
    def __init__(self, name):
        self.name = name
#    def __repr__(self):
#        #network = sac(Network).get_by(id=network_id)
#        return '<%s: %s>' % (
#            self.name,
#            Session.query(Network).filter_by(id=self.network_id).all()[0].name
#        )
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



bots = sqla.Table('bots', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('nick', sqla.Unicode, nullable=False, unique=True),
    sqla.Column('name', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('passwd', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('volatile', sqla.Boolean, nullable=False, default=True)
)

bot_association = sqla.Table('bot_association', metadata,
    sqla.Column('bot_id', sqla.Integer, sqla.ForeignKey('bots.id')),
    sqla.Column('user_id', sqla.Integer, sqla.ForeignKey('users.id'))
)

class Bot(object):
    def __init__(self, nick, name=None, passwd=None, volatile=False):
        self.nick = nick
        self.name = name
        self.passwd = passwd
        self.volatile = volatile

    def __unicode__(self):
        return self.nick

#    def __repr__(self):
#        return '<%r: Owned by %r>' % (
#            self.name,
#            Session.query(User).filter_by(id=self.user_id).first().name
#        )

    def has_network(self, address):
        return address in [network.address for network in self.networks]

    def get_network(self, address):
        for network in self.networks:
            if network.address == address:
                return network
        return None


events = sqla.Table('events', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('channel_id', sqla.Integer, sqla.ForeignKey('channels.id')),
    sqla.Column('stamp', UTCDateTime, nullable=False, unique=False),
    sqla.Column('type', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('subtype', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('source', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('msg', sqla.Unicode, nullable=False, unique=False),
)

#event_association = sqla.Table('event_association', metadata,
#    sqla.Column('event_id', sqla.Integer, sqla.ForeignKey('events.id')),
#    sqla.Column('network_id', sqla.Integer, sqla.ForeignKey('networks.id')),
#    sqla.Column('channel_id', sqla.Integer, sqla.ForeignKey('channels.id'))
#)

class Event(object):
    def __init__(self, type, source, message):
        self.source = source
        self.msg = message
        self.type = type
        self.stamp = UTC.localize(datetime.datetime.utcnow())
    def __unicode__(self):
        return self.msg
    def __repr__(self):
        return '<%s: (%s %s) %r>' % (self.type, self.stamp, self.msg)

class AutoUpdateExtension(sqla.orm.MapperExtension):
    def before_insert(self, mapper, connection, instance):
        try:
            instance.modified = UTC.localize(datetime.datetime.utcnow())
        except:
            print 2222, mapper, connection, instance

    def before_update(self, mapper, connection, instance):
        try:
            instance.modified = UTC.localize(datetime.datetime.utcnow())
        except:
            print 2222, mapper, connection, instance



mapper(User, users, order_by=[sqla.asc(users.c.name)])
#       ,
#       properties={'bots': relation(Bot, backref='owner',
#                                    secondary=user_association,
#                                    cascade="all, delete, delete-orphan")})

mapper(Network, networks, extension=AutoUpdateExtension(),
       properties = {'channels': relation(Channel,
                                          backref='network',
                                          secondary=channel_association,
                                          cascade="all, delete, delete-orphan"),
                     'modified_by': relation(User, backref='networks',
                                             secondary=network_modifiers)},
       order_by=[sqla.asc(networks.c.name)])

mapper(Channel, channels,
       properties = {'events': relation(Event,
                                        backref='channel')},
       order_by=[sqla.asc(channels.c.name)])

mapper(Bot, bots,
       properties = {'channels': relation(Channel,
                                          backref='bot',
                                          secondary=channel_association,
                                          cascade="all, delete, delete-orphan"),
                     'networks': relation(Network,
                                          backref='bot',
                                          secondary=network_association),
                     'owner': relation(User,
                                       backref='bots',
                                       secondary=user_association)},
       order_by=[sqla.asc(bots.c.nick)]
       )

mapper(Event, events, order_by=[sqla.asc(events.c.stamp)])