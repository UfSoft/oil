import logging

from oil.lib.base import *
from oil.model.fe import schemas as schema

log = logging.getLogger(__name__)

class BotsController(BaseController):

    def __before__(self):
        if not c.user:
            redirect_to(controller='account', action='signin')

    def index(self):
        return render('bots.index')

    @rest.dispatch_on(POST="register_POST")
    def register(self):
        return render('bots.register')

    @validate(template='bots.register', schema=schema.RegisterBot(),
              form='register', variable_decode=True)
    def register_POST(self):
        post = request.POST.copy()
#        if model.Session.query(model.Bot).filter_by(name=post['name']).first():
#            session['message'] = _('A bot with that name is already registred.')
#            session.save()
#            redirect_to(action='index')
        log.debug('on register bot post')
        bot = model.Bot(post['name'])
        c.user.bots.append(bot)
        model.Session.save(c.user)
        model.Session.commit()
        redirect_to(action='edit', id=post['name'])

    @rest.dispatch_on(POST="edit_POST")
    def edit(self, id):
        c.bot = model.Session.query(model.Bot).filter_by(name=id).first()
        #c.bot = model.Session.query(model.Bot).get(id)
        return render('bots.edit')

    @validate(template='bots.edit', schema=schema.UpdateBot(),
              form='register', variable_decode=True)
    def edit_POST(self, id):
        log.debug(self.form_result)
        #bot = model.Session.query(model.Bot).get(id)
        bot = model.Session.query(model.Bot).filter_by(name=id).first()
        log.debug(bot.__dict__)
        bot.name = self.form_result['name']
        model.Session.update(bot)
        model.Session.commit()
        redirect_to(action='index', id=None)

    @rest.dispatch_on(POST="delete_POST")
    def delete(self, id):
        c.bot = model.Session.query(model.Bot).get(int(id))
        return render('bots.delete')

    def delete_POST(self, id):
        bot = model.Session.query(model.Bot).get(int(id))
        bot.delete_children()
        model.Session.delete(bot)
        model.Session.commit()
        redirect_to(action='index', id=None)
