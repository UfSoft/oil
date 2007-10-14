from oil.bots.tests import *

class TestBotController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='bot'))
        # Test response...
