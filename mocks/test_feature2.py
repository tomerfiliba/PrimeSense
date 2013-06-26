import logging

logger = logging.getLogger("crayola")

class TestFeature2(object):
    def test_spam(self):
        logger.info("i am spam")

    def test_eggs(self):
        logger.info("i am eggs")
        1/0


