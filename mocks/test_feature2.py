import logging

logger = logging.getLogger("crayola")

class TestFeature2(object):
    def setUp(self):
        logger.info("hello")
    
    def tearDown(self):
        logger.info("goodbye")
    
    def test_spam(self):
        logger.info("i am spam")

    def test_eggs(self):
        logger.info("i am eggs")
        self.report_error_links = [("log", "c:\\foo\\bar.txt")]
        1/0


