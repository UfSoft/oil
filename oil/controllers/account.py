import logging

from oil.lib.base import *
from openid.consumer.consumer import Consumer, SUCCESS, FAILURE, DiscoveryFailure
from openid import sreg
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
        sreg_request = sreg.SRegRequest(
            #required=['email'],
            optional=['fullname', 'timezone', 'language', 'email']
        )

        authrequest.addExtension(sreg_request)
        #authrequest.addExtensionArg('http://specs.openid.net/sreg/2.0:sreg', 'optional', 'fullname')
        redirecturl = authrequest.redirectURL(h.url_for('/', qualified=True),
            #h.url_for(controller='main', action='index', qualified=True),
            return_to=h.url_for(action='verified', qualified=True),
            immediate=False
        )
        session['openid_session'] = self.openid_session
        session.save()
        return redirect_to(redirecturl)

    def verified(self):
        problem_msg = _('A problem ocurred comunicating to your OpenID server. '
                        'Please try again.')
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
            sreg_response = sreg.SRegResponse.fromSuccessResponse(info)
            user.name = sreg_response.get('fullname', u'')
            user.email = sreg_response.get('email', u'')
            user.tzinfo = sreg_response.get('timezone', u'')
            log.debug('sreg lang: %r' % sreg_response.get('language', u''))
#            #data = info.extensionResponse('sreg', True)
#            if sreg_response and sreg_response.has_key('fullname') and len(sreg_response['fullname']) > 0:
#                user.name = sreg_response['fullname']
#            if sreg_response and sreg_response.has_key('email') and len(sreg_response['email']) > 0:
#                user.email = sreg_response['email']
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
