import logging

from oil.bots.controllers import *

log = logging.getLogger(__name__)

class BotController(BaseController):

    def index(self, id):
        # Return a rendered template
        #   return render('/some/template.mako')
        # or, Return a response
        return model.Session.query(model.Bot).get(int(id)).name

    def name(self, id):
        bot = model.Session.query(model.Bot).get(int(id))
        if bot:
            return bot.name
        return 'Unrecognizable bot'

    def whereami(self):
        log.debug('on whereami')
        return h.url_for('/', qualified=True)

    def reload(self):
        g.ircnw.reload()

    def part(self, botname, network, channel):
        bot = g.ircnw.get_bot(botname)
        network = bot.get_network(int(network))
        network.part(channel)

