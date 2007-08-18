import logging

from oil.lib.base import *
from oil.model.fe import schemas as schema

log = logging.getLogger(__name__)

class AdminController(BaseController):

    def __before__(self):
        if not c.user:
            #log.info('No user')
            session['redirected_from'] = h.url_for(qualified=True)
            session.save()
            redirect_to(controller='account', action='signin')
        if not c.user.is_admin():
            #log.info('Not admin')
            session['message'] = _("You are not an Administrator")
            session.save()
            redirect_to(controller='logs', action='index', id=None)

    def index(self):
        c.networks = len(model.Session.query(model.Network).all())
        c.channels = len(model.Session.query(model.Channel).all())
        return render('admin.index')

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
        log.info('on add network POST')
        sac_q = model.Session.query(model.Network)
        network = model.Network(request.POST['address'], request.POST['port'])
        network.name = request.POST['name']
        sac_q.session.flush()
        redirect_to(action='edit_network', id=request.POST['name'])

    @rest.dispatch_on(POST='edit_network_POST')
    def edit_network(self, id):
        c.network = model.Session.query(model.Network).get_by(name=id)
        return render('admin.edit_network')

    def edit_network_POST(self, id):
        network = model.Session.query(model.Network).get_by(name=id)
        vars = request.POST.copy()
        network.name = vars['name']
        network.address = vars['address']
        network.port = vars['port']
        channels = request.POST.getall('channels')
        for channel in network.channels:
            if not channel.name in channels:
                model.Session.session.delete(channel)
        for channel in channels:
            if not network.has_channel(channel):
                network.channels.append(model.Channel(channel))
        model.Session.session.commit()
        redirect_to(action='networks')
