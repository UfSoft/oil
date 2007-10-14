import logging

from oil.lib.base import *

log = logging.getLogger(__name__)

class LangController(BaseController):

    def index(self):
        # The lang choose behind the scenes is done on base.py
        # Here we just redirect to the previous page if that was set or to the
        # main page.
        if 'current_url' in request.POST:
            redirect_to(str(request.POST['current_url']))
        redirect_to(controller='main')
