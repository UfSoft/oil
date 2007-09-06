import logging

from boil.controllers import *

log = logging.getLogger(__name__)

class BotsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py file has
    # a resource setup:
    #     map.resource('bot', 'bots')


    def index(self, format='html'):
        """GET /bots: All items in the collection."""
        # url_for('bots')
        pass

    def create(self):
        """POST /bots: Create a new item."""
        # url_for('bots')
        abort(501) # Raise Not Implemented

    def new(self, format='html'):
        """GET /bots/new: Form to create a new item."""
        # url_for('new_bot')
        abort(501) # Raise Not Implemented

    def update(self, id):
        """PUT /bots/id: Update an existing item."""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(h.url_for('bot', id=ID),
        #           method='put')
        # url_for('bot', id=ID)
        abort(501) # Raise Not Implemented

    def delete(self, id):
        """DELETE /bots/id: Delete an existing item."""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(h.url_for('bot', id=ID),
        #           method='delete')
        # url_for('bot', id=ID)
        abort(501) # Raise Not Implemented

    def show(self, id, format='html'):
        """GET /bots/id: Show a specific item."""
        # url_for('bot', id=ID)
        pass

    def edit(self, id, format='html'):
        """GET /bots/id;edit: Form to edit an existing item."""
        # url_for('edit_bot', id=ID)
        abort(501) # Raise Not Implemented
