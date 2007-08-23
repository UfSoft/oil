import logging

from oil.lib.base import *
from oil.model.fe import schemas as schema

log = logging.getLogger(__name__)

class AdminController(BaseController):

    def __before__(self):
        if not c.user:
            #log.debug('No user')
            session['redirected_from'] = h.url_for(qualified=True)
            session.save()
            redirect_to(controller='account', action='signin')
        if not c.user.is_admin():
            #log.debug('Not admin')
            session['message'] = _("You are not an Administrator")
            session.save()
            redirect_to(controller='logs', action='index', id=None)

    def index(self):
        c.networks = len(model.Session.query(model.Network).all())
        c.channels = len(model.Session.query(model.Channel).all())
        return render('admin.index')
    #---- Handle Bots ---------------------------------------------------------

    def bots(self):
        c.bots = model.Session.query(model.Bot).all()
        return render('admin.bots')

    @rest.dispatch_on(POST='add_bot_POST')
    def add_bot(self):
        return render('admin.add_bot')

    @validate(template='admin.add_bot', schema=schema.AddBot(), form='add_bot',
              variable_decode=True)
    def add_bot_POST(self):
        post = request.POST.copy()
        bot = model.Bot(post['nick'], post['name'], post['passwd'], False)
        model.Session.save(bot)
        model.Session.commit()
        redirect_to(action='edit_bot', id=post['nick'])

    @rest.dispatch_on(POST='edit_bot_POST')
    def edit_bot(self, id):
        c.bot = model.Session.query(model.Bot).filter_by(name=id).first()
        return render('admin.edit_bot')

    def edit_bot_POST(self, id):
        pass

    #---- Handle Networks -----------------------------------------------------
    def networks(self):
        c.networks = model.Session.query(model.Network).all()
        return render('admin.networks')

    @rest.dispatch_on(POST='add_network_POST')
    def add_network(self):
        print 'on add network'
        return render('admin.add_network')

    @validate(template='admin.add_network', schema=schema.AddNetwork(),
                form='add_network', variable_decode=True)
    def add_network_POST(self):
        log.debug('on add network POST')
        network = model.Network(request.POST['address'], request.POST['port'])
        network.name = request.POST['name']
        model.Session.save(network)
        model.Session.commit()
        redirect_to(action='edit_network', id=request.POST['name'])

    @rest.dispatch_on(POST='edit_network_POST')
    def edit_network(self, id):
        c.network = model.Session.query(model.Network).filter_by(name=id).first()
        return render('admin.edit_network')

    def edit_network_POST(self, id):
        network = model.Session.query(model.Network).filter_by(name=id).first()
        vars = request.POST.copy()
        network.name = vars['name']
        network.address = vars['address']
        network.port = vars['port']
        channels = request.POST.getall('channels')
        for channel in network.channels:
            if not channel.name in channels:
                model.Session.delete(channel)
        for channel in channels:
            if not network.has_channel(channel):
                network.channels.append(model.Channel(channel))
        model.Session.commit()
        redirect_to(action='networks')
