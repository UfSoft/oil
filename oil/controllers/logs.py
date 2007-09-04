import logging
import datetime
from oil.lib.base import *
import pytz

log = logging.getLogger(__name__)

class LogsController(BaseController):

    def index(self):
        c.networks = model.Session.query(model.Network).all()
        log.debug(c.networks)
        return render('logs.index')

    def view(self, network, channel, year=None, month=None, day=None):
        if not network and not channel:
            return self.index()
        c.date = pytz.UTC.localize(datetime.datetime.utcnow())
        channel_participation = model.Session.query(model.ChannelParticipation) \
            .filter_by(network_name=network, channel_name=channel ).first()
        c.topic = channel_participation.channel.topic
        c.events = model.Session.query(model.ChannelEvent) \
            .filter_by(channel_participation_id=channel_participation.id).all()
#        c.network = channel_participation.network_name
#        c.channel = channel_participation.channel_name
        c.url = h.url_for('feed_logs', network=channel_participation.network_name,
                          channel=channel_participation.channel_name,
                          qualified=True)
        return render('logs.view')
