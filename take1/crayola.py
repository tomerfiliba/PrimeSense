import logging
from primelib import openni2, _openni2 as c_api
import time


logger = logging.getLogger("crayola")

class ExtendedDevice(openni2.Device):
    def soft_reset(self):
        self.set_property(c_api.XN_MODULE_PROPERTY_RESET, c_api.XnParamResetType.XN_RESET_TYPE_SOFT)
        #self._reopen()
        
    def hard_reset(self):
        self.set_property(c_api.XN_MODULE_PROPERTY_RESET, c_api.XnParamResetType.XN_RESET_TYPE_POWER)
        time.sleep(6)
        self._reopen()
    
    def set_usb_bulk(self):
        self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE, 
            c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_BULK_ENDPOINTS)

    def set_usb_iso(self):
        self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE, 
            c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_ISO_ENDPOINTS)


_the_device = None
def _get_device():
    global _the_device
    if _the_device is None:
        openni2.initialize()
        openni2.configure_logging("./logs", 1)
        _the_device = ExtendedDevice.open_any()
    else:
        _the_device._reopen()
    return _the_device


class CrayolaTestBase(object):
    @classmethod
    def setUpClass(cls):
        cls.logger = logger
    
    def setUp(self):
        self.device = _get_device()
    
    def general_read_correctness(self, frames):
        pass














