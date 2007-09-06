from oil.tests import *

class TestNetworksController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='networks'))
        # Test response...
