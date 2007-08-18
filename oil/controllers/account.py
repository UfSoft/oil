import logging

from oil.lib.base import *
from openid.consumer.consumer import Consumer, SUCCESS, FAILURE, DiscoveryFailure
from datetime import datetime

log = logging.getLogger(__name__)

class AccountController(BaseController):
    def __before__(self):
        self.openid_session = session.get("openid_session", {})

    @rest.dispatch_on(POST="update_account")
    def index(self):
        if not c.user:
            redirect_to(action='signin')
        return render('account.index')

    def update_account(self):
        if 'language' in request.POST:
            redirect_to(action='index', id=None)
        print request.POST
        query = model.Session.query(model.User)
        user = query.get_by(openid=request.POST['openid'])
        user.name = request.POST['name']
        user.tzinfo = request.POST['tzinfo']
        model.Session.commit()
        redirect_to(action='index')

    @rest.dispatch_on(POST="signin_POST")
    def signin(self):
        if c.user:
            session['message'] = _('Already signed in.')
            session.save()
            redirect_to(action='index')
        return render('account.signin')

    def signin_POST(self):
        self.consumer = Consumer(self.openid_session, g.openid_store)
        openid = request.params.get('openid', None)
        if openid is None:
            return render('account.signin')
        try:
            authrequest = self.consumer.begin(openid)
        except DiscoveryFailure, e:
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
            log.info('on verified before sassion check')
            if 'redirected_from' in session:
                url = session['redirected_from']
                del(session['redirected_from'])
                session.save()
                return redirect_to(url)
            return redirect_to(controller='logs', action='index', id=None)
        else:
            session['message'] = _('A problem ocurred comunicating to '
                                   'your OpenID server. Please try again.')
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
