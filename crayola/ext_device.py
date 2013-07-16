import time
from primesense import openni2, _openni2 as c_api


class ExtendedDevice(openni2.Device):
    """
    This class extends the basic OpenNI Device class with extra non-public APIs, 
    used for testing purposes
    """
    
    def soft_reset(self):
        """
        performs a soft-reset of the device
        """
        self.set_property(c_api.XN_MODULE_PROPERTY_RESET, c_api.XnParamResetType.XN_RESET_TYPE_SOFT)
        #self._reopen()
        
    def hard_reset(self, sleep = 6):
        """
        performs a hard-reset of the device (also takes care of sleeping a little and reopening 
        the device)
        """
        self.set_property(c_api.XN_MODULE_PROPERTY_RESET, c_api.XnParamResetType.XN_RESET_TYPE_POWER)
        time.sleep(sleep)
        self._reopen()
    
    def set_usb_bulk(self):
        """
        puts the device in USB bulk mode
        """
        self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE, 
            c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_BULK_ENDPOINTS)

    def set_usb_iso(self):
        """
        puts the device in USB ISO mode
        """
        self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE, 
            c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_ISO_ENDPOINTS)


