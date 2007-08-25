from oil.tests import *

class TestLangController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='lang'))
        # Test response...
