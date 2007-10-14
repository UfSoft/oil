import logging
import irclib
from oil import db as model
#from pylons.i18n import ugettext as _

log = logging.getLogger(__name__)

#irclib.DEBUG = True

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
        self.channels = self.get_channels()
        #self.address = "%s:%s" % (self.network.address, self.network.port)
        self.populate_events()

    def get_channels(self):
        channels = {}
        for cp in self.nw.channel_participation:
            channels[cp.channel.channel_name] = cp.id
            #channels[cp.channel.name]['id'] = cp.id
        return channels

    def populate_events(self):
        for event in irclib.generated_events + irclib.protocol_events:
            if event not in ['privnotice', 'ctcp', 'topic', 'join', 'part',
                             'disconnect', 'ping', 'mode']:
                self.connection.add_global_handler(event, self.dispatcher)
#        self.ircobj.add_global_handler('topic', self.on_topic, -10)
#        self.ircobj.add_global_handler('ctcp', self.on_ctcp, -10)
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
                log.error('Failed to connect to %s:%s, retrying...'
                          % (self.network.address, self.network.port))
                self.connect()
        while not self.is_connected():
            pass
        self.join_channels()

    def join_channels(self):
        for channel in self.channels.keys():
            self.connection.join("#%s" % channel)

    def dispatcher(self, connection, event):
        print 'on dispatcher'
        etype = event.eventtype()
        try:
            source = irclib.nm_to_n(event.source())
        except:
            source = event.source()
        target = event.target().lstrip('#')
        message = ''.join(event.arguments())
        #print repr(type), repr(source), repr(target), repr(message)
        log.debug("%s %s %s %s" % (repr(etype), repr(source), repr(target), repr(message)))
        self.write_event(target, etype, source, message)

    def on_ctcp(self, c, e):
        args = e.arguments()
        if args[0] == 'VERSION':
            #print 'on ctcp VERSION'
            log.debug('on ctcp VERSION')
            self.connection.ctcp_reply(irclib.nm_to_n(e.source()),
                                       'OIL 0.1')
        elif args[0] == 'ACTION':
            channel = e.target().lstrip('#')
            source = irclib.nm_to_n(e.source())
            message = args[1]
            print channel, 'ctcp', source, args[1], args[0]
            #self.send_event(channel, 'ctcp', source, args[1], subtype=args[0])
            self.write_event(channel, 'ctcp', source, args[1], subtype=args[0])

    def on_topic(self, c, e):
        #print c.__dict__
        args = e.arguments()
        if len(args) < 2:
            channel = e.target().lstrip('#')
            topic = args[0]
        else:
            channel = args[0].lstrip('#')
            topic = args[1]
#        print 'target: ', e.target()
#        print 'source: ', e.source()
#        print args
        channel_participation_id = self.channels[channel]
        channel = model.Session.query(model.ChannelParticipation) \
            .get(channel_participation_id).channel
        if channel.topic != topic:
            log.debug('Topic for channel #%s changed, updating DB' % channel)
            channel.topic = topic
            model.Session.save(channel)
            model.Session.commit()
        model.Session.remove()

    def on_join_and_part(self, c, e):
        join_msg = _("%s joined %s")
        part_msg = _("%s parted %s")
        try:
            nick = irclib.nm_to_n(e.source())
        except:
            nick = e.source()
        channel = e.target().lstrip('#')
        type = e.eventtype()
        if type == 'join':
            message = join_msg % (nick, channel)
        elif type == 'part':
            message = part_msg % (nick, channel)
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
            channel_participation_id = self.channels[channel.lstrip('#')]
        except KeyError, e:
            print e
            return
        channel_participation = model.Session.query(model.ChannelParticipation) \
            .get(channel_participation_id)
        #channel_participation.add_event(type, source, message, subtype)
        event = model.ChannelEvent(channel_participation, type, source, message, subtype or u'')
        model.Session.save(event)
        model.Session.commit()

    def process(self):
        if not self.is_connected():
            self.connect()
        else:
            self.ircobj.process_once(1)

    def quit(self):
        for channel in self.channels.keys():
            self.connection.part("#%s" % channel, message="I'll stop logging now")
        self.connection.disconnect(message="I'll stop logging now")

class IRCBot(object):
    def __init__(self, db_bot_instance, baseurl=None):
        self.bot = db_bot_instance
        self.baseurl = baseurl

        self.nps = [IRCNetworkParticipation(np, baseurl=baseurl) for
                    np in db_bot_instance.network_participation]

    def connect_all(self):
        for np in self.nps:
            np.connect()

    def process_all(self):
        for np in self.nps:
            np.process()

    def quit(self):
        for np in self.nps:
            np.quit()

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
