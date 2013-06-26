from primelib import openni2
import time


_the_device = None
def get_device():
    global _the_device
    if not _the_device:
        openni2.initialize()
        time.sleep(3)
        _the_device = openni2.Device.open_any()
    return _the_device


class OniTest(object):
    @classmethod
    def setUpClass(cls):
        openni2.initialize()
        cls.device = get_device()




