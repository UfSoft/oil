import logging

from oil.lib.base import *
from oil.model.fe import schemas as schema

log = logging.getLogger(__name__)

class NetworksController(BaseController):

    def __before__(self):
        if not c.user:
            redirect_to(controller='account', action='signin')

    def index(self):
        # Return a rendered template
        #   return render('/some/template.mako')
        # or, Return a response
        return 'Hello World'

    @rest.dispatch_on(POST="add_POST")
    def add(self, id):
        c.bot = model.Session.query(model.Bot).filter_by(name=id).first()
        return render('networks.add')

    @validate(template='networks.add', schema=schema.AddNetwork(),
              form='add', variable_decode=True)
    def add_POST(self, id):
        bot = model.Session.query(model.Bot).filter_by(name=self.form_result['name']).first()
        post = request.POST.copy()
        query = model.Session.query(model.Network)
        network = query.filter_by(address=self.form_result['address'],
                                  port=self.form_result['port']).first()
        log.debug(network)
        if not network:
            network = model.Network(address=self.form_result['address'],
                                    port=self.form_result['port'])
            model.Session.save(network)
            model.Session.commit()
        query = model.Session.query(model.NetworkParticipation)
        participation = query.filter_by(bot_id=bot.id,
                                        network_name=network.name).first()
        if participation:
            session['message'] = _('Network already registred for this bot. '
                                   'No need for duplicates')
            session.save()
            redirect_to(controller='bots', action='edit', id=bot.name)
        participation = model.NetworkParticipation(bot, network,
                                                   self.form_result['nick'])
        model.Session.save(participation)
        model.Session.commit()
        redirect_to('edit_network', bot=self.form_result['name'],
                    network=network.name)

    @rest.dispatch_on(POST="edit_POST")
    def edit(self, nick, network):
        network = model.Session.query(model.Network).get(network)
        query = model.Session.query(model.NetworkParticipation)
        c.participation = query.filter_by(nick=nick,
                                          network_name=network.name).first()
        log.debug(c.participation)
        return render('networks.edit')

    @validate(template='networks.edit', schema=schema.UpdateNetwork(),
              form='edit')
    def edit_POST(self, nick, network):
        log.debug('on networks edit_POST')
        log.debug(self.form_result)
        participation = model.Session.query(model.NetworkParticipation) \
            .get(self.form_result['participation_id'])
        log.debug(participation)
        participation.nick = self.form_result['nick']
        if 'clear_passwd' in self.form_result and \
            self.form_result['clear_passwd'] == 1:
            log.debug('clear passwd is %s' % self.form_result['clear_passwd'])
            participation.passwd = u''
        elif self.form_result['passwd']:
            # Only change password if there's anything submited
            participation.passwd = self.form_result['passwd']
        model.Session.save(participation)
        model.Session.commit()
        redirect_to(controller='bots', action='index')
