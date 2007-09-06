from oil.tests import *

class TestChannelsController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='channels'))
        # Test response...
