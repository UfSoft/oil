import logging

from oil.lib.base import *
import pylons

log = logging.getLogger(__name__)

class AjaxController(BaseController):

    #@jsonify
    def networks(self, id):
        search_str = '%' + request.GET['q'].strip() + '%'
        query = model.Session.query(model.Network)
        if search_str:
            c.networks = query.filter(
                model.networks.c.address.like(search_str)
            )
        else:
            c.networks = query.all()
        pylons.response.headers['Content-Type'] = "text,xml"
        return render('ajax.networks', format="xml")
