import logging

from oil.lib.base import *
from oil.model.fe import schemas as schema

log = logging.getLogger(__name__)

class BotsController(BaseController):

    def index(self):
        return render('bots.index')

    @rest.dispatch_on(POST="register_POST")
    def register(self):
        return render('bots.register')

    @validate(template='bots.register', schema=schema.RegisterBot(),
              form='register', variable_decode=True)
    def register_POST(self):
        post = request.POST.copy()
        if model.Session.query(model.Bot).filter_by(nick=post['nick']).first():
            session['message'] = _('A bot with that nick is already registred.')
            session.save()
            redirect_to(action='index')
        bot = model.Bot(post['name'], post['nick'], post['passwd'])
        c.user.bots.append(bot)
        model.Session.save(c.user)
        model.Session.commit()
        redirect_to(action='index')

    def edit(self, id):
        c.bot = model.Session.query(model.Bot).filter_by(nick=id).first()
        return render('bots.edit')



