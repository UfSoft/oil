import logging

from oil.web.lib.base import *

log = logging.getLogger(__name__)

class MainController(BaseController):

    def index(self):
        return render('main.index')
