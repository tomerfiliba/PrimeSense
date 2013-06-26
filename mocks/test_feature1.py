import logging

logger = logging.getLogger("crayola")

class TestFeature1(object):
    def test_foo(self):
        logger.info("i am foo")

    def test_bar(self):
        logger.info("i am bar")
        assert False

