from pylons import config
import sqlalchemy as sqla
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm import scoped_session, sessionmaker
import datetime
from pytz import UTC
import logging

log = logging.getLogger(__name__)

# Global session manager.
# Session() returns the session object appropriate for the current web request.
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
        self.signup = UTC.localize(datetime.datetime.utcnow())
        #self.signup = datetime.datetime.utcnow()
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

    def delete_children(self):
        user_bots = Session.query(Bot).filter_by(user_id=self.id).all()
        for bot in user_bots:
            Session.delete(bot)


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
    sqla.Column('channel_key', sqla.Unicode, nullable=True),
    sqla.Column('channel_prefix', sqla.String(3), nullable=False),
    sqla.Column('first_entry', sqla.DateTime(timezone=True), nullable=True, unique=False),
    sqla.Column('last_entry', sqla.DateTime(timezone=True), nullable=True, unique=False),
    sqla.PrimaryKeyConstraint('network_name', 'channel_name')
)

class Channel(object):
    def __init__(self, network, name):
        self.network = network
        self.channel_name = name

    def __repr__(self):
        return "<IRC Channel: '%s'>" % self.channel_name

    def __unicode__(self):
        return self.channel_name

    def update_last_entry(self, date):
        if not self.first_entry:
            self.first_entry = date
        self.last_entry = date
        log.debug('updated last entry date')


channel_participations = sqla.Table('channel_participations', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('network_name', sqla.Unicode),
    sqla.Column('channel_name', sqla.Unicode),
    sqla.Column('network_participations_id', sqla.Integer,
                sqla.ForeignKey('network_participations.id')),
    sqla.ForeignKeyConstraint(['network_name','channel_name'],
                              ['channels.network_name','channels.channel_name'],
                              name='channel_participation_fk')
)

sqla.Index('channel_participations_idx', channel_participations.c.network_name,
           channel_participations.c.channel_name,
           channel_participations.c.network_participations_id)

class ChannelParticipation(object):
    def __init__(self, network_participation, channel_instance):
        self.network_participation = network_participation
        self.channel = channel_instance
    def __repr__(self):
        return '<ChannelParticipation: "%r" "%r">' % (self.channel,
                                                    self.network_participation)
    def add_event(self, type, source, message, subtype=None):
        log.debug('adding new channel event')
        event = ChannelEvent(self, type, source, message, subtype)
        Session.save(event)
        Session.commit()

    def delete_children(self):
        log.debug('deleting events for channel #%s' % self.channel.channel_name)
        channel_events_for_channel_participation = Session.query(ChannelEvent) \
            .filter_by(channel_participation_id=self.id)
        for event in channel_events_for_channel_participation:
            Session.delete(event)
        log.debug('deleted events for channel #%s' % self.channel.channel_name)
        Session.delete(self.channel)
        log.debug('deleted channel #%s' % self.channel.channel_name)
#        Session.commit()

    def get_events_for(self, day):
        start = datetime.datetime(day.year, day.month, day.day, 0, 0, 1, 1, day.tzinfo)
        end = datetime.datetime(day.year, day.month, day.day, 23, 59, 59, 999999, day.tzinfo)
        return Session.query(ChannelEvent).filter(
            channel_events.c.channel_participation_id == self.id
        ).filter(channel_events.c.stamp.between(start, end)).all()

channel_topics = sqla.Table('channel_topics', metadata,
    sqla.Column('channel_participation_id', None,
                sqla.ForeignKey('channel_participations.id'),
                primary_key=True),
    sqla.Column('topic', sqla.Unicode, unique=False, nullable=False),
#    sqla.Column('changed_on', sqla.DateTime(timezone=True), unique=False),
#    sqla.Column('changed_by', sqla.Unicode, unique=False),

)

class ChannelTopic(object):
    def __init__(self, channel_participation, topic):
        self.channel_participation = channel_participation
        self.topic = topic

    def __repr__(self):
        return "<ChannelTopic: '%s' on %s%s>" % \
            (self.topic, self.channel_participation.channel.channel_prefix,
             self.channel_participation.channel.channel_name)

channel_topic_infos = sqla.Table('channel_topic_infos', metadata,
    sqla.Column('channel_participation_id', None,
                sqla.ForeignKey('channel_participations.id'),
                primary_key=True),
    sqla.Column('changed_on', sqla.DateTime(timezone=True), unique=False, nullable=False),
    sqla.Column('changed_by', sqla.Unicode, unique=False, nullable=False),

)

class ChannelTopicInfo(object):
    def __init__(self, channel_participation, changed_by, changed_on):
        self.channel_participation = channel_participation
        self.changed_by = changed_by
        if not isinstance(changed_on, float):
            changed_on = float(changed_on)
        self.changed_on = UTC.localize(
            datetime.datetime.utcfromtimestamp(changed_on)
        )

    def __repr__(self):
        return "<ChannelTopicInfo: topic for %s%s changed by %s on %s>" % \
            (self.channel_participation.channel.channel_prefix,
             self.channel_participation.channel.channel_name,
             self.changed_by, self.changed_on)

channel_events = sqla.Table('channel_events', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('channel_participation_id', None,
                sqla.ForeignKey('channel_participations.id')),
    #sqla.Column('channel_name', sqla.Unicode)
    sqla.Column('stamp', sqla.DateTime(timezone=True), nullable=False, unique=False),
    sqla.Column('type', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('subtype', sqla.Unicode, nullable=True, unique=False),
    sqla.Column('source', sqla.Unicode, nullable=False, unique=False),
    sqla.Column('msg', sqla.Unicode, nullable=False, unique=False),
)

class ChannelEvent(object):
    def __init__(self, channel_participation, type, source, message, subtype=None):
        self.channel_participation = channel_participation
        self.channel_participation_id = channel_participation.id
        self.type = type
        self.subtype = subtype
        self.source = source
        self.msg = message
        self.stamp = UTC.localize(datetime.datetime.utcnow())
        self.channel_participation.channel.update_last_entry(self.stamp)
        Session.save(self.channel_participation.channel)

    def __unicode__(self):
        return self.msg

    def __repr__(self):
        return "<ChannelEvent: (%s) %s(%s) - %s - %s>" % (self.stamp, self.type,
                                                          self.subtype,
                                                          self.source,
                                                          self.msg)

live_bots = sqla.Table('bot_networks', metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, autoincrement=True),
    sqla.Column('bot_name', None, sqla.ForeignKey('bots.name')),
    sqla.Column('url', sqla.String, nullable=False, unique=True),
)

class LiveBot(object):
    def __init__(self, bot):
        self.bot = bot
        self.bot_name = bot.name
        self.url = None

    def __repr__(self):
        return "<LiveBot: %s on %s>" % (self.bot.name, self.url)


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
            network = relation(Network, backref='network_participation'),
            bot = relation(Bot, backref='network_participation')
       )

)

mapper(Channel, channels,
       order_by=[sqla.asc(channels.c.network_name)],
       properties=dict(
            network=relation(Network, backref='channels'),
       )
)

mapper(ChannelParticipation, channel_participations,
       order_by=[sqla.asc(channel_participations.c.network_participations_id)],
       properties=dict(
            network_participation=relation(NetworkParticipation,
                                           backref='channel_participation'),
            #network=relation(Channel, backref='bots_on_chans'),
            channel=relation(Channel, backref='channel_participation'),
       )
)

mapper(ChannelTopic, channel_topics,
       properties=dict(
            channel_participation = relation(ChannelParticipation,
                                             backref=sqla.orm.backref(
                                                'channel_topic', uselist=False)
                                             ),
       )
)

mapper(ChannelTopicInfo, channel_topic_infos,
       properties=dict(
            channel_participation = relation(ChannelParticipation,
                                             backref=sqla.orm.backref(
                                                'channel_topic_info',
                                                uselist=False)
                                             ),
       )
)

mapper(ChannelEvent, channel_events,
       order_by=[sqla.asc(channel_events.c.channel_participation_id),
                sqla.asc(channel_events.c.stamp)],
       properties=dict(
            channel_participation=relation(ChannelParticipation,
                                           backref='events')
       )
)

mapper(LiveBot, live_bots,
#       properties=dict(
#           bot = relation(Bot, backref='online')
#       )
)
