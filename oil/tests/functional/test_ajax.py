from oil.tests import *

class TestAjaxController(TestController):

    def test_index(self):
        response = self.app.get(url_for(controller='ajax'))
        # Test response...
