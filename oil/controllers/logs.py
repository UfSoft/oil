import logging
import datetime
#from babel.util import LOCALTZ, UTC
from oil.lib.base import *

log = logging.getLogger(__name__)

class LogsController(BaseController):

    def __before__(self):
        c.monthNames = g.locale.months['format']['wide'].values()
        c.weekDays = g.locale.days['format']['abbreviated'].values()

    def index(self):
        return render('logs.index')

    def view_networks(self):
        log.info('On VIEW NETWORKS')
        c.networks = model.Session.query(model.Network).all()
        return render('logs.view_networks')

    def view_network(self, network):
        log.info('On VIEW NETWORK!')

    def view_channel(self, network, channel):
        pass

    def view(self, network=None, channel=None, year=None, month=None, day=None):
        currdate = datetime.date.today()
        selected = {}
        selected['year'] = int(year or currdate.year)
        selected['month'] = int(month or currdate.month)
        selected['day'] = int(day or currdate.day)
        c.selected = selected
        c.baseurl = h.url_for(action='view', network=network, channel=channel,
                              year=None, month=None, day=None, qualified=True)
#        log.info('%s %s %s %s' %(network, channel, year, month, day))
        #print network, channel, year, month, day
        network_ = model.Session.query(model.Network).filter_by(name=network).first()
        channel_ = model.Session.query(model.Channel).filter_by(network_id=network_.id).first()
        #print network
#        date = datetime.datetime.now(LOCALTZ)
#        print date
#        date = date.replace(year=int(year), month=int(month),
#                                   day=int(day))
#        print date
#        #date.year = int(year)
#        #date.month = int(month)
#        #date.day = int(day)
#        c.date = date
        #print date
        c.date = datetime.date(year=int(year or currdate.year),
                               month=int(month or currdate.month),
                               day=int(day or currdate.day)) #, tzinfo=UTC)
        #print c.date.year, c.date.month, c.date.day
        messages = model.Session.query(model.Event).filter_by(channel_id=channel_.id)
        c.minDate = channel_.first_entry
        c.maxDate = channel_.last_entry
        #messages = messages.filter_by(date=c.date)
        c.topic = channel_.topic
        c.messages = messages
        for message in messages:
            log.info(repr(message.stamp))
            #log.info(message.time)
        #print list(c.messages)
        #c.minDate = messages[0].date
        #c.maxDate = messages[-1:][0].date
        #print messages[-1:][0].msg
        return render('logs.view')
        #return render('logs.Copy_of_view')