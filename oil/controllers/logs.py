import logging

from oil.lib.base import *

log = logging.getLogger(__name__)

class LogsController(BaseController):

    def index(self):
        return render('logs.index')

    view = index
