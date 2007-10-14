import logging
import datetime
from oil.lib.base import *
import pytz

log = logging.getLogger(__name__)

class LogsController(BaseController):

    def index(self):
        c.networks = model.Session.query(model.Network).all()
        log.debug(c.networks)
        return render('logs.index')

    def view(self, network, channel, year=None, month=None, day=None):
        if not network and not channel:
            return self.index()
        if c.user:
            tzinfo = pytz.timezone(c.user.tzinfo)
        else:
            tzinfo = pytz.UTC
        now = datetime.datetime.utcnow()
        if year or month or day:
            year = int(year) if year else now.year
            month = int(month) if month else now.month
            day = int(day) if day else now.day
            c.date = tzinfo.localize(datetime.datetime(year, month, day))
        else:
            c.date = tzinfo.localize(now)
        channel_participation = model.Session.query(model.ChannelParticipation) \
            .filter_by(network_name=network, channel_name=channel ).first()
        c.channel_participation = channel_participation
        c.events = channel_participation.get_events_for(c.date)

        # Get all dates which have log entries
        calendar_dates_select = model.sqla.select(
            [model.sqla.cast(model.channel_events.c.stamp, model.sqla.Date)],
            model.channel_events.c.channel_participation_id == channel_participation.id,
            distinct=True
        )
        c.calendar_dates = [ date[0] for date in
            model.Session.execute(calendar_dates_select).fetchall()
        ]
        #c.calendar_dates = set([date[0].date() for date in calendar_dates])
        c.monthNames = g.locale.months['format']['wide'].values()
        c.weekDays = g.locale.days['format']['abbreviated'].values()
        c.minDate = channel_participation.channel.first_entry
        c.maxDate = channel_participation.channel.last_entry
        c.url = h.url_for('feed_logs', network=channel_participation.network_name,
                          channel=channel_participation.channel_name,
                          qualified=True)
        c.baseurl = h.url_for('logs', network=channel_participation.network_name,
                          channel=channel_participation.channel_name,
                          qualified=True)
        return render('logs.view')
