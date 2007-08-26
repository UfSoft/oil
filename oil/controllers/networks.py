import logging

from oil.lib.base import *
from oil.model.fe import schemas as schema

log = logging.getLogger(__name__)

class NetworksController(BaseController):

    def index(self):
        # Return a rendered template
        #   return render('/some/template.mako')
        # or, Return a response
        return 'Hello World'

    @rest.dispatch_on(POST="add_POST")
    def add(self, id):
        c.bot = model.Session.query(model.Bot).filter_by(nick=id).first()
        return render('networks.add')

    @validate(template='networks.add', schema=schema.AddNetwork(),
              form='add', variable_decode=True)
    def add_POST(self, id):
        bot = model.Session.query(model.Bot).filter_by(nick=id).first()
        post = request.POST.copy()
        query = model.Session.query(model.Network)
        network = query.filter_by(address=post['address'], port=post['port']).first()
        log.debug(network)
        if not network:
            network = model.Network(address=post['address'], port=post['port'])
            model.Session.save(network)
            model.Session.commit()
            log.debug(network)
            log.debug(network.id)
            network = query.get(network.id)
        if network in bot.networks:
            session['message'] = _('Network already registred for this bot. '
                                   'No need for duplicates')
            session.save()
            redirect_to(controller='bots', action='edit', id=bot.nick)
        bot.networks.append(network)
        model.Session.save(bot)
        model.Session.commit()
        redirect_to('edit_network', bot=bot.nick, network=network.name)

    @rest.dispatch_on(POST="edit_POST")
    def edit(self, bot, network):
        query = model.Session.query(model.Network).filter(
            model.Network.bots.any(nick=bot)
        )
        #c.bot = model.Session.query(model.Bot).filter_by(nick=bot).first()
        c.network = query.filter_by(name=network).first()
        return render('networks.edit')

    @validate(template='networks.edit', schema=schema.UpdateNetwork(),
              form='edit')
    def edit_POST(self, bot, network):
        log.debug('on networks edit_POST')
        query = model.Session.query(model.Network).filter(
            model.Network.bots.any(nick=bot)
        )
        #c.bot = model.Session.query(model.Bot).filter_by(nick=bot).first()
        network = query.filter_by(name=network).first()
        if not self.form_result['channels']:
            self.form_result['channels'] = []
        network.channels = [
            model.Channel(channel) for channel in self.form_result['channels']
        ]
        model.Session.save(network)
        model.Session.commit()
        redirect_to(controller='bots', action='index')
