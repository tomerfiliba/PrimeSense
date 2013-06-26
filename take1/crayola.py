import logging
from primelib import openni2, _openni2 as c_api


logger = logging.getLogger("crayola")


class SensorConfig(object):
    USB_BULK = 0
    USB_ISO = 1
    
    def __init__(self, usb_mode = None, depth = None, ir = None, image = None):
        if usb_mode not in (None, self.USB_ISO, self.USB_BULK):
            raise ValueError("Invalid USB mode")
        for tup in [depth, ir, image]:
            if tup is not None and (len(tup) != 3 or any(not isinstance(x, int) for x in tup)):
                raise ValueError("Expected a 3-tuple, got %r" % (depth,))
        self.depth = depth
        self.ir = ir
        self.image = image
        self.usb_mode = usb_mode
    
    def apply(self, device):
        if self.usb_mode is not None:
            if self.usb_mode == self.USB_BULK:
                mode = c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_BULK_ENDPOINTS
            else:
                mode = c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_ISO_ENDPOINTS
            self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE, mode)


class ExtendedDevice(openni2.Device):
    def configure(self, config):
        config.apply(self)

    def soft_reset(self):
        self.invoke(c_api.PS_COMMAND_SOFT_RESET, None, 0)
    def hard_reset(self):
        self.invoke(c_api.PS_COMMAND_POWER_RESET, None, 0)


_the_device = None
def _get_device(cls):
    global _the_device
    if _the_device is None:
        openni2.initialize()
        _the_device = ExtendedDevice.open_any()
    return _the_device


class CrayolaTestBase(object):
    @classmethod
    def setUpClass(cls):
        cls.logger = logger
        cls.device = _get_device()
    
    def general_read_correctness(self, frames):
        pass














