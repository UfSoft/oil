import logging
import irclib
from oil import db as model
from UserDict import DictMixin
from pytz import UTC
from datetime import datetime
#from pylons.i18n import ugettext as _

log = logging.getLogger(__name__)

#irclib.DEBUG = True

VERSION = __import__('pkg_resources').get_distribution('OilBots').version

CHANNEL_PREFIXES = ['&', '#', '!', '+']

def _(str):
    return str

class IRCNetworkParticipation(object):
    def __init__(self, db_network_instance, baseurl=None):
        self.nw = db_network_instance
        self.nick = self.nw.nick
        self.passwd = self.nw.passwd
        self.name = self.nw.bot.name
        if baseurl:
            self.name += " logging on %s" % baseurl
        self.network = self.nw.network
        self.ircobj = irclib.IRC()
        self.connection = self.ircobj.server()
        self.pool = self.connection.pool
        self.channels = self._get_channels()
        self.populate_events()

    def _get_channels(self):
        channels = {}
        for cp in self.nw.channel_participation:
            channels[cp.channel.channel_name] = cp.id
        return channels

    def get_channel(self, channel_name):
        try:
            return self.channels[channel_name]
        except KeyError:
            return None

    def populate_events(self):
        for event in irclib.generated_events + irclib.protocol_events:
            if event not in ['privnotice', 'ctcp', 'topic', 'join', 'part',
                             'disconnect', 'ping', 'mode']:
                self.connection.add_global_handler(event, self.dispatcher)
        self.connection.add_global_handler('topicinfo', self.on_topicinfo, 10)
        self.connection.add_global_handler('currenttopic', self.on_currenttopic, 10)
        self.connection.add_global_handler('notopic', self.on_notopic, 10)
        self.connection.add_global_handler('topic', self.on_topic, 10)
        self.connection.add_global_handler('ctcp', self.on_ctcp)
        self.connection.add_global_handler('join', self.on_join_and_part)
        self.connection.add_global_handler('part', self.on_join_and_part)
        self.connection.add_global_handler('namreply', self.on_namreply)

    def is_connected(self):
        return self.connection.is_connected()

    def connect(self):
        if not self.is_connected():
            try:
                self.connection.connect(server=self.network.address,
                                        port=self.network.port,
                                        nickname=self.nick,
                                        ircname=self.name,
                                        password=self.passwd)
            except irclib.ServerConnectionError, error:
                log.error('Failed to connect to %s:%s: %s, retrying...'
                          % (self.network.address, self.network.port, error))
                self.connect()
        while not self.is_connected():
            pass
        self._join_channels()

    def _join_channels(self):
        for channel in self.channels.keys():
            channel_participation_id = self.channels[channel]
            channel = model.Session.query(model.ChannelParticipation) \
                .get(channel_participation_id).channel
            self.connection.join("%s%s" % (channel.channel_prefix,
                                           channel.channel_name))

    def join_channel(self, channel_prefix, channel_name):
        self.connection.join("%s%s" % (channel_prefix, channel_name))

    def dispatcher(self, connection, event):
        print 'on dispatcher'
        etype = event.eventtype()
        try:
            source = irclib.nm_to_n(event.source())
        except:
            source = event.source()
        target = event.target().lstrip(''.join(CHANNEL_PREFIXES))
        message = u''.join(event.arguments())
        #print repr(type), repr(source), repr(target), repr(message)
        log.debug("%s %s %s %s" % (repr(etype), repr(source), repr(target),
                                   repr(message)))
        self.write_event(target, etype, source, message)

    def on_ctcp(self, c, e):
        args = e.arguments()
        if args[0] == 'VERSION':
            #print 'on ctcp VERSION'
            log.debug('on ctcp VERSION')
            self.connection.ctcp_reply(irclib.nm_to_n(e.source()),
                                       'OIL %s' % VERSION)
        elif args[0] == 'ACTION':
            channel = e.target().lstrip(''.join(CHANNEL_PREFIXES))
            source = irclib.nm_to_n(e.source())
            message = args[1]
            print channel, 'ctcp', source, args[1], args[0]
            #self.send_event(channel, 'ctcp', source, args[1], subtype=args[0])
            self.write_event(channel, 'ctcp', source, args[1], subtype=args[0])

    def on_topic(self, c, e):
        args = e.arguments()
        if len(args) < 2:
            channel = e.target().lstrip(''.join(CHANNEL_PREFIXES))
            topic = args[0]
        else:
            channel = args[0].lstrip(''.join(CHANNEL_PREFIXES))
            topic = args[1]
        changed_by = irclib.nm_to_n(e.source())
        channel_participation_id = self.channels[channel]
        channel_participation = model.Session.query(model.ChannelParticipation) \
            .get(channel_participation_id)
        channel_topic = model.Session.query(model.ChannelTopic) \
                        .get(channel_participation_id)
        channel = channel_participation.channel
        if not channel_topic:
            log.debug("Setting topic for channel %s%s by %s." % \
                      (channel.channel_prefix, channel.channel_name, changed_by))
            channel_topic = model.ChannelTopic(channel_participation, topic)
            model.Session.save(channel_topic)
            model.Session.commit()
        elif channel_topic.topic != topic:
            log.debug('Topic for channel %s%s changed by %s, updating DB' % \
                      (channel.channel_prefix, channel.channel_name, changed_by))
            channel_topic.topic = topic
            model.Session.save(channel_topic)
            model.Session.commit()

        channel_topic_info = model.Session.query(model.ChannelTopicInfo) \
                            .get(channel_participation_id)

        changed_on = UTC.localize(datetime.utcnow())

        if not channel_topic_info:
            log.debug('on_topic ChannelTopicInfo for %s non-existant' % channel)
            channel_topic_info = model.ChannelTopicInfo(channel_participation,
                                                        changed_by, changed_on)
        else:
            if channel_topic_info.changed_by != changed_by or \
                channel_topic_info.changed_on != changed_on:
                log.debug(self.__class__.__name__ +
                          ' updating topic info for channel %s...' % channel)
                if channel_topic_info.changed_by != changed_by:
                    channel_topic_info.changed_by = changed_by
                if channel_topic_info.changed_on != changed_on:
                    channel_topic_info.changed_on = changed_on
        model.Session.save(channel_topic_info)
        model.Session.commit()

        message = "%s changed the topic to '%s'" % (changed_by, topic)
        self.write_event(channel.channel_name, 'topic', '*****', message)

        model.Session.remove()

    def on_currenttopic(self, c, e):
        model.Session.remove()
        args = e.arguments()
        if len(args) < 2:
            channel = e.target().lstrip(''.join(CHANNEL_PREFIXES))
            topic = args[0]
        else:
            channel = args[0].lstrip(''.join(CHANNEL_PREFIXES))
            topic = args[1]

        channel_participation_id = self.channels[channel]
        channel_participation = model.Session.query(model.ChannelParticipation) \
            .get(channel_participation_id)
        channel_topic = model.Session.query(model.ChannelTopic) \
                        .get(channel_participation_id)
        if not channel_topic:
            log.debug('on_currenttopic ChannelTopic for %s non-existant' % channel)
            channel_topic = model.ChannelTopic(channel_participation, topic)
        else:
            if channel_topic.topic != topic:
                log.debug(self.__class__.__name__ + ' updating topic for channel %s...' % channel)
                channel_topic.topic = topic

        model.Session.save(channel_topic)
        model.Session.commit()

    def on_topicinfo(self, c, e):
        model.Session.remove()
        args = e.arguments()
        log.debug(args)
        channel = args[0].lstrip(''.join(CHANNEL_PREFIXES))
        changed_by = args[1]
        changed_on = UTC.localize(datetime.utcfromtimestamp(float(args[2])))

        channel_participation_id = self.channels[channel]
        channel_participation = model.Session.query(model.ChannelParticipation) \
            .get(channel_participation_id)
        channel_info = model.Session.query(model.ChannelTopicInfo) \
                        .get(channel_participation_id)
        if not channel_info:
            log.debug('on_topicinfo ChannelTopicInfo for %s non-existant' % channel)
            channel_info = model.ChannelTopicInfo(channel_participation,
                                                  changed_by, changed_on)
        else:
            if channel_info.changed_by != changed_by or \
                channel_info.changed_on != changed_on:
                log.debug(self.__class__.__name__ + ' updating topic info for channel %s...' % channel)
                if channel_info.changed_by != changed_by:
                    channel_info.changed_by = changed_by
                if channel_info.changed_on != changed_on:
                    channel_info.changed_on = changed_on
        model.Session.save(channel_info)
        model.Session.commit()

    def on_notopic(self, c, e):
        return
        args = e.arguments()
        channel = args[0].lstrip(''.join(CHANNEL_PREFIXES))
        channel_participation_id = self.channels[channel]
        channel_ = model.Session.query(model.ChannelParticipation) \
            .get(channel_participation_id).channel
        channel_.topic = ''
        model.Session.save(channel_)
        model.Session.commit()
        model.Session.remove()

    def on_join_and_part(self, c, e):
        join_msg = _("%s joined %s")
        part_msg = _("%s parted %s")
        msg = _("%%s %s %%s")
        try:
            nick = irclib.nm_to_n(e.source())
        except:
            nick = e.source()
        channel = e.target().lstrip(''.join(CHANNEL_PREFIXES))
        type = e.eventtype()
        if type == 'join':
            message = msg % 'join' % (nick, channel)
        elif type == 'part':
            message = msg % 'part' % (nick, channel)
        if nick not in (self.name, self.nick) and channel in self.channels.keys():
            # Only log part's and joins which are not mine
            self.write_event(channel, type, '*****', message)
        self.connection.names(['#%s'%channel])
#        log.debug("users on %s: %s" % (channel, ))

    def on_namreply(self, c, e):
        log.debug('namreply for channel %r -> type: %s source: %s target: %s'
                  % (e.arguments()[1], e.eventtype(), e.source(), e.target()))
        log.debug([nick for nick in e.arguments()[2].split()])

    def on_error(self, c, e):
        log.error(e.arguments())

    def write_event(self, channel, type, source, message, subtype=None):
        log.debug("writing event -> channel: %r type: %r source: %r message: %r subtype: %r"
                  % (channel, type, source, message, subtype))
        model.Session.remove()
        try:
            channel_participation_id = self.channels[channel.lstrip(''.join(CHANNEL_PREFIXES))]
        except KeyError, e:
            print e
            return
        channel_participation = model.Session.query(model.ChannelParticipation) \
            .get(channel_participation_id)
        event = model.ChannelEvent(channel_participation, type, source,
                                   message, subtype or u'')
        model.Session.save(event)
        model.Session.commit()

    def process(self):
        if not self.is_connected():
            self.connect()
        else:
            self.ircobj.process_once(1)

    def quit(self):
        for channel in self.channels.keys():
            channel_participation_id = self.channels[channel]
            channel = model.Session.query(model.ChannelParticipation) \
                .get(channel_participation_id).channel
            self.connection.part("%s%s" % (channel.channel_prefix,
                                           channel.channel_name),
                                 message="I'll stop logging now")
        self.connection.disconnect(message="I'll stop logging now")

class IRCBot(object):
    def __init__(self, db_bot_instance, baseurl=None):
        self.bot = db_bot_instance
        self.baseurl = baseurl

        self.nps = []
        self._update_nps()

    def _update_nps(self):
        self.nps = [IRCNetworkParticipation(np, baseurl=self.baseurl) for
                    np in self.bot.network_participation
                    if np not in self.nps]
    def connect_all(self):
        for np in self.nps:
            np.connect()

    def process_all(self):
        for np in self.nps:
            np.process()

    def quit(self):
        for np in self.nps:
            np.quit()

    def reload(self):
        log.debug(self.__class__.__name__ + ' reloading')
        self.get_networks()
        for nps in self.nps:
            nps.quit()
        self.connect_all()

    def get_networks(self):
        self.nps = [IRCNetworkParticipation(np, baseurl=self.baseurl) for
                    np in self.bot.network_participation]

class IRCBotsNetwork(object):
    def __init__(self, baseurl=None):
        self.bots = {}
        self.baseurl = baseurl
        bots = model.Session.query(model.Bot).filter(
            model.network_participations.c.bot_id==model.bots.c.id).all()
        for bot in bots:
            self.bots[bot.name] = IRCBot(bot, baseurl=baseurl)

    def connect_all(self):
        for bot in self.bots.values():
            bot.connect_all()

    def process_all(self):
        while True:
            for bot in self.bots.values():
                bot.process_all()

    def quit(self):
        for bot in self.bots.values():
            bot.quit()

    def _get_bots(self):
        bots = model.Session.query(model.Bot).filter(
            model.network_participations.c.bot_id==model.bots.c.id).all()
        for bot in bots:
            self.bots[bot.name] = IRCBot(bot, baseurl=self.baseurl)

    def get_bot(self, botname):
        try:
            return self.bots[botname]
        except KeyError:
            return None

    def reload(self):
        log.debug(self.__class__.__name__ + ' reloading')
        self._get_bots()
        for bot in self.bots.values():
            bot.reload()
