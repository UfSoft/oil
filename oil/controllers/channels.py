import logging

from oil.lib.base import *
from oil.model.fe import schemas as schema

log = logging.getLogger(__name__)

class ChannelsController(BaseController):

    def index(self):
        # Return a rendered template
        #   return render('/some/template.mako')
        # or, Return a response
        return 'Hello World'

    @rest.dispatch_on(POST="add_POST")
    def add(self, nick, network):
        query = model.Session.query(model.NetworkParticipation)
        c.participation = query.filter_by(nick=nick,
                                          network_name=network).first()
        return render('channels.add')

    @validate(template='channels.add', schema=schema.AddChannel(),
              form='add', variable_decode=True)
    def add_POST(self, nick, network):
        log.debug(self.form_result)
        query = model.Session.query(model.NetworkParticipation)
        participation = query.filter_by(nick=nick,
                                        network_name=network).first()

#        channnel_participation = model.Session.query(model.ChannelParticipation) \
#            .filter_by(network_participations_id=participation.id) \
#            .filter_by(channel_name=self.form_result['channel']).first()
        channnel_participation = model.Session.query(model.ChannelParticipation) \
            .filter_by(channel_name=self.form_result['channel'])

        if channnel_participation \
            .filter_by(network_participations_id=participation.id).first():
            log.debug(channnel_participation)
            session['message'] = _('Channel %s already on %s channel list' %
                                   (self.form_result['channel'],
                                    participation.nick))
            session.save()
            redirect_to('edit_network', nick=participation.nick,
                        network=participation.network.name)
        elif channnel_participation.first():
            log.debug(channnel_participation)
            session['message'] = _('Channel %s already on the channel list '
                                   'of another bot, %s' %
                                   (self.form_result['channel'],
                                    channnel_participation.first() \
                                        .network_participation.nick))
            session.save()
            redirect_to('edit_network', nick=participation.nick,
                        network=participation.network.name)

        channnel_participation = model.ChannelParticipation(
            participation, model.Channel(participation.network,
                                         self.form_result['channel'])
        )
        model.Session.save(channnel_participation)
        model.Session.commit()
        redirect_to('edit_network', nick=participation.nick,
                    network=participation.network.name)

    @rest.dispatch_on(POST="delete_POST")
    def delete(self, id, channel):
        query = model.Session.query(model.ChannelParticipation)
        c.participation = query.filter_by(network_participations_id=int(id),
                                          channel_name=channel).first()
        return render('channels.delete')

    def delete_POST(self, id, channel):
        query = model.Session.query(model.ChannelParticipation)
        participation = query.filter_by(network_participations_id=int(id),
                                        channel_name=channel).first()

        network_participation = participation.network_participation
        redirect_url = h.url_for('edit_network',
                                 nick=network_participation.nick,
                                 network=network_participation.network.name)
        model.Session.delete(participation)
        model.Session.commit()
        redirect_to(redirect_url)

