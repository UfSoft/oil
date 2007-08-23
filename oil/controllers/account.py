import logging

from oil.lib.base import *
from openid.consumer.consumer import Consumer, SUCCESS, FAILURE, DiscoveryFailure
from datetime import datetime
from oil.model.fe import schemas as schema

log = logging.getLogger(__name__)

class AccountController(BaseController):
    def __before__(self):
        self.openid_session = session.get("openid_session", {})

    @rest.dispatch_on(POST="update_account")
    def index(self):
        if not c.user:
            redirect_to(action='signin')
        return render('account.index')

    @validate(template='account.index', schema=schema.UpdateUser(), form='index',
              variable_decode=True)
    def update_account(self):
        if 'language' in request.POST:
            redirect_to(action='index', id=None)
        print request.POST
        query = model.Session.query(model.User)
        user = query.filter_by(openid=request.POST['openid']).first()
        user.name = request.POST['name']
        if 'email' in request.POST:
            user.email = request.POST['email']
        user.tzinfo = request.POST['tzinfo']
        #user.language = request.POST['language']
        model.Session.commit()
        redirect_to(action='index')

    @rest.dispatch_on(POST="signin_POST")
    def signin(self):
        if c.user:
            session['message'] = _('Already signed in.')
            session.save()
            redirect_to(action='index')
        session.clear()
        return render('account.signin')

    def signin_POST(self):
        problem_msg = _('A problem ocurred comunicating to your OpenID server. '
                        'Please try again.')
        if g.development_mode:
            # Fake the openid request
            session.clear()
            session.save()
            log.info('In development mode 1')
            openid = request.params.get('openid', None)
            session['openid'] = openid
            session.save()
            redirect_to(action='index')

        self.consumer = Consumer(self.openid_session, g.openid_store)
        openid = request.params.get('openid', None)
        if openid is None:
            session['message'] = problem_msg
            session.save()
            return render('account.signin')
        try:
            authrequest = self.consumer.begin(openid)
        except DiscoveryFailure, e:
            session['message'] = problem_msg
            session.save()
            return redirect_to(action='signin')
        redirecturl = authrequest.redirectURL(h.url_for('/', qualified=True),
            #h.url_for(controller='main', action='index', qualified=True),
            return_to=h.url_for(action='verified', qualified=True),
            immediate=False
        )
        session['openid_session'] = self.openid_session
        session.save()
        return redirect_to(redirecturl)

    def verified(self):
        self.consumer = Consumer(self.openid_session, g.openid_store)
        info = self.consumer.complete(request.params,
                                      (h.url_for(controller='account',
                                                 action='verified',
                                                 qualified=True)))
        if info.status == SUCCESS:
            query = model.Session.query(model.User)
            user = query.filter_by(openid=info.identity_url).first()
            if user is None:
                user = model.User(info.identity_url)
                #model.Session.save(user)
            if user.banned:
                redirect_to(action='banned')
            user.updatelastlogin()
            model.Session.save(user)
            model.Session.commit()
            session.clear()
            session['openid'] = info.identity_url
            session.save()
            log.debug('on verified before session check')
            if 'redirected_from' in session:
                url = session['redirected_from']
                del(session['redirected_from'])
                session.save()
                return redirect_to(url)
            return redirect_to(controller='logs', action='index', id=None)
        else:
            session['message'] = problem_msg
            session.save()
            return redirect_to(action='signin')

    def signout(self):
        if not c.user:
            session['message'] = _("You are not signed in.")
            session.save()
            redirect_to(controller='logs', action='index', id=None)
        session.clear()
        session['message'] = _("You've been signed out.")
        session.save()
        redirect_to(controller='logs', action='index', id=None)

    def banned(self):
        if not c.user:
            session['message'] = _("You are not signed in.")
            session.save()
            redirect_to(action='signin')
        if not c.user.banned:
            session['message'] = _("You are not banned.")
            session.save()
            redirect_to(action='index')
        return render('account.banned')

    @rest.dispatch_on(POST="register_bot_POST")
    def register_bot(self):
        return render('account.register_bot')

    @validate(template='account.register_bot', schema=schema.RegisterBot(),
              form='register_bot', variable_decode=True)
    def register_bot_POST(self):
        post = request.POST.copy()
        #host, port = post['network'].split(':')
        bot = model.Bot(post['name'], post['nick'], post['passwd'])
        user = model.Session.query(model.User).filter_by(id=post['user_id']).first()
        user.bots.append(bot)
        model.Session.save(bot)
        model.Session.save(user)
        model.Session.commit()
        redirect_to(action='edit_bot', id=bot.name)

    @rest.dispatch_on(POST="edit_bot_POST")
    def edit_bot(self, id):
        c.bot = model.Session.query(model.Bot).filter_by(nick=id).first()
        return render('account.edit_bot')

    @validate(template='account.edit_bot', schema=schema.UpdateBot(),
              form='edit_bot', variable_decode=True)
    def edit_bot_POST(self, id):
        bot = model.Session.query(model.Bot).filter_by(name=id).first()
        print 11
        results = self.form_result
        bot.name = results['name']
        bot.nick = results['nick']
        if 'passwd' in results and results['passwd']:
            bot.passwd = results['passwd']

#        query = model.Session.query(model.Network)
#        networks = []
#        for name, addr, port in results['networks']:
#            network = query.filter_by(address=addr, port=port).first()
#            if not network:
#                network = model.Network(addr, port)
#            network.name = name
#            networks.append(network)
#        bot.networks = networks
        model.Session.save(bot)
        model.Session.commit()
        redirect_to(action='index', id=None)

    @rest.dispatch_on(POST="add_network_POST")
    def add_network(self, bot):
        c.bot = model.Session.query(model.Bot).filter_by(nick=bot).first()
        return render('account.add_network')

    @validate(template='account.add_network', schema=schema.AddNetwork(),
              form='add_network')
    def add_network_POST(self, bot):
        bot = model.Session.query(model.Bot).filter_by(nick=bot).first()
        if bot not in c.user.bots:
            c.user.bots.append(bot)
        network = model.Session.query(model.Network).filter_by(
            address=self.form_result['address'],
            port=self.form_result['port'],
            name=self.form_result['name']).first()
        if not network:
            network = model.Network(self.form_result['address'],
                                    self.form_result['port'],
                                    self.form_result['name'])
        else:
            network.address = self.form_result['address']
            network.port = self.form_result['port']
            network.name = self.form_result['name']

        if network not in bot.networks:
            bot.networks.append(network)
        if network not in c.user.networks:
            c.user.networks.append(network)
        model.Session.save(c.user)
        model.Session.save(network)
        model.Session.save(bot)
        model.Session.commit()
        redirect_to(action='edit_network', bot=bot.nick, network=network.name)


    def edit_network(self, bot, network):
        query = model.Session.query(model.Network).filter_by(name=network)
        c.network = query.filter(model.bots.c.name==bot).first()
        c.bot = c.network.bot[0]
        return render('account.edit_network')

    @rest.dispatch_on(POST="edit_channels_POST")
    def edit_channels(self, bot, network):
        query = model.Session.query(model.Network).filter_by(name=network)
        c.network = query.filter(model.bots.c.name==bot).first()
        return render('account.edit_channels')

    @validate(template='account.edit_channels', schema=schema.UpdateChannels(),
              form='edit_channels', variable_decode=True)
    def edit_channels_POST(self, bot, network):
        log.debug('channels post for bot %s and net %s' % (network,bot))
        query = model.Session.query(model.Network).filter_by(name=network)
        network = query.filter(model.bots.c.name==bot).first()
#        query = model.Session.
        def filter(result):
            if result is None:
                return result
            return model.Session.query(result).filter(model.sqla.sql.and_(
                                    model.networks.c.name==network,
                                    model.bots.c.name==bot))
        channels = []
        query = model.Session.query(model.Channel).filter(
            model.channels.c.network_id==network.id
        )
        for entry in self.form_result['channels']:
            channel = query.filter_by(name=entry).first()
            if not channel:
                channel = model.Channel(entry)
            channels.append(channel)
        log.debug(channels)
        network.channels = channels
        model.Session.save(network)
        model.Session.commit()
        redirect_to(action='index')


