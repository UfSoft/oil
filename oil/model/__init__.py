from pylons import config
#from oil.lib.helpers import url_for
#from sqlalchemy import Column, MetaData, Table, types
import sqlalchemy as sqla
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.associationproxy import association_proxy
import datetime
from pytz import UTC

# http://dpaste.com/17837/
#

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
    sqla.Column('openid', sqla.String, unique=True),
    sqla.Column('name', sqla.Unicode(60), nullable=False, unique=True),
    sqla.Column('slug', sqla.String),
    sqla.Column('signup', sqla.DateTime(timezone=True), nullable=False),
    sqla.Column('lastlogin', sqla.DateTime(timezone=True), nullable=False),
    sqla.Column('email', sqla.Unicode, nullable=True, unique=False), #, unique=True),
    sqla.Column('banned', sqla.Boolean, nullable=False, default=False),
    sqla.Column('type', sqla.String(7), nullable=False, default="user"),
    sqla.Column('language', sqla.Unicode, nullable=True, default="en"),
    sqla.Column('tzinfo', sqla.Unicode, nullable=True, default="UTC"),

)

class User(object):
    def __init__(self, openid, name=None):
        self.openid = openid
        self.name = name if name is not None else openid
        #self.signup = UTC.localize(datetime.datetime.utcnow())
        self.signup = datetime.datetime.utcnow()
        self.updatelastlogin()
    def __unicode__(self):
        return self.name
    def __repr__(self):
        return "<User: %s (%s)>" % (self.name, self.openid)
    def updatelastlogin(self):
        self.lastlogin = UTC.localize(datetime.datetime.utcnow())
        #self.lastlogin = datetime.datetime.utcnow()
    def is_admin(self):
        return self.type == 'admin'
    def is_manager(self):
        return self.type == 'manager'


bots = sqla.Table('bots', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('name', sqla.Unicode, nullable=False, unique=True), #, primary_key=True),
    sqla.Column('user_id', sqla.Integer, sqla.ForeignKey('users.id'))
)

class Bot(object):
    def __init__(self, name):
        self.name = name

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return "<IRC Bot: %s>" % self.name

    def delete_children(self):
        network_participations_for_bot = Session.query(NetworkParticipation) \
            .filter_by(bot_id=self.id).all()
        for participation in network_participations_for_bot:
            participation.delete_children()
            Session.delete(participation)


networks = sqla.Table('networks', metadata,
    sqla.Column('name', sqla.Unicode, nullable=False, unique=True, primary_key=True),
    sqla.Column('address', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('port', sqla.Integer, nullable=False, unique=False),
)

class Network(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.name = u'%s-%s' % (address, port)
    def __unicode__(self):
        return '%s:%s' % (self.address, self.port)
    def __repr__(self):
        return '<IRC Network: %s:%s>' % (self.address, self.port)

network_participations = sqla.Table('network_participations', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('network_name', None, sqla.ForeignKey('networks.name')),
    sqla.Column('bot_id', None, sqla.ForeignKey('bots.id')),
    sqla.Column('nick', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('passwd', sqla.Unicode, nullable=True, unique=False),
)
sqla.Index('network_participations_idx', network_participations.c.network_name,
           network_participations.c.bot_id)

class NetworkParticipation(object):
    def __init__(self, bot, network, nick=None):
        self.bot = bot
        self.network = network
        self.nick = nick
    def __repr__(self):
        return "<NetworkParticipation: %s (%s on %s:%s)>" % (self.nick,
                                                          self.bot.name,
                                                          self.network.address,
                                                          self.network.port)
    def delete_children(self):
        channel_participations_for_network = Session.query(ChannelParticipation) \
            .filter_by(network_participations_id=self.id).all()
        for participation in channel_participations_for_network:
            participation.delete_children()
            Session.delete(participation)


channels = sqla.Table('channels', metadata,
    sqla.Column('network_name', None, sqla.ForeignKey('networks.name'),
                primary_key=True),
    sqla.Column('channel_name', sqla.Unicode, primary_key=True),
    sqla.Column('topic', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('first_entry', sqla.Date, nullable=True, unique=False),
    sqla.Column('last_entry', sqla.Date, nullable=True, unique=False),
    sqla.PrimaryKeyConstraint('network_name', 'channel_name')
)

class Channel(object):
    def __init__(self, network, name):
        self.network = network
        self.channel_name = name

    def __repr__(self):
        return "<IRC Channel: '%s'>" % self.channel_name
#        network = Session.query(Network).filter_by(id=self.network.name).first()
#        return "<IRC Channel: '%s' on '%s:%d'>" % (
#            self.name, self.network.address, self.network.port
#        )

    def __unicode__(self):
        return self.channel_name


channel_participations = sqla.Table('channel_participations', metadata,
    sqla.Column('network_name', sqla.Unicode),
    sqla.Column('channel_name', sqla.Unicode),
    sqla.Column('network_participations_id', sqla.Integer,
                sqla.ForeignKey('network_participations.id')),
    sqla.PrimaryKeyConstraint('network_participations_id','network_name','channel_name',
                              name='channel_participation_pk'),
    sqla.ForeignKeyConstraint(['network_name','channel_name'],
                              ['channels.network_name','channels.channel_name'],
                              name='channel_participation_fk')
)

class ChannelParticipation(object):
    def __init__(self, network_participation, channel_instance):
        self.network_participation = network_participation
        self.channel = channel_instance
    def __repr__(self):
        return '<ChannelParticipation: "%r" "%r">' % (self.channel,
                                                    self.network_participation)

    def delete_children(self):
        # TODO: Delete event's for channel participation
        Session.delete(self.channel)

mapper(User, users, order_by=[sqla.asc(users.c.name)])


mapper(Bot, bots, order_by=[sqla.asc(bots.c.name)],
       properties=dict(
            manager=relation(User, backref='bots'),
            #networks=relation(NetworkParticipation, backref='bots')
       )
)

mapper(Network, networks,
#       properties=dict(
#            bots=relation(Bot, backref='networks')
#       )
)

mapper(NetworkParticipation, network_participations,
       order_by=[sqla.asc(network_participations.c.id)],
       properties=dict(
            #channels=relation(ChannelParticipation, backref='bot'),
            network = relation(Network, backref='network_participation',
                               cascade="all, delete-orphan"),
            bot = relation(Bot, backref='network_participation')
       )

)

mapper(Channel, channels,
       order_by=[sqla.asc(channels.c.network_name)],
       properties=dict(
            network=relation(Network, backref='channels',
                             cascade="all, delete-orphan"),
       )
)

mapper(ChannelParticipation, channel_participations,
       order_by=[sqla.asc(channel_participations.c.network_participations_id)],
       properties=dict(
            network_participation=relation(NetworkParticipation,
                                           backref='channel_participation'),
            #network=relation(Channel, backref='bots_on_chans'),
            channel=relation(Channel, backref='channel_participation',
                             cascade="all, delete-orphan"),
       )
)
