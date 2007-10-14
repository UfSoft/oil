import logging

from oil.bots.controllers import *

log = logging.getLogger(__name__)

class BotController(BaseController):

    def index(self):
        # Return a rendered template
        #   return render('/some/template.mako')
        # or, Return a response
        return model.Session.query(model.Bot).get(1).name
        return 'Hello World'
