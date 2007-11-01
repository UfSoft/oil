import logging

from oil.web.lib.base import *
import pylons

log = logging.getLogger(__name__)

class FeedController(BaseController):

    def index(self):
        # Return a rendered template
        #   return render('/some/template.mako')
        # or, Return a response
        return 'Hello World'

    def logs(self, network, channel):
        channel_participation = model.Session.query(model.ChannelParticipation) \
            .filter_by(network_name=network, channel_name=channel ).first()
        network=channel_participation.network_name
        channel=channel_participation.channel_name
        c.url = h.url_for('feed_logs', network=network, channel=channel,
                          qualified=True)
        c.logs_url = h.url_for('logs', network=network, channel=channel)
        c.topic = channel_participation.channel_topic.topic
        if not c.topic:
            c.topic = "Logs for #%s on %s" % (channel, network.replace('-', ':'))

        c.events = model.Session.query(model.ChannelEvent) \
            .filter_by(channel_participation_id=channel_participation.id).all()

        pylons.response.headers['Content-Type'] = "text/xml"
        return render('feed.logs', format="xml")
