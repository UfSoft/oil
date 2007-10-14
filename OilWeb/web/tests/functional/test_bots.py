from oil.tests import *

class TestBotsController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='bots'))
        # Test response...
