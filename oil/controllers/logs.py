import logging
import datetime
from oil.lib.base import *
import pytz

log = logging.getLogger(__name__)

class LogsController(BaseController):

    def index(self):
        c.networks = model.Session.query(model.NetworkParticipation).all()
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
        return render('logs.view')
