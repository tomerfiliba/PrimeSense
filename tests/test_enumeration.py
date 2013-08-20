

from crayola import CrayolaTestBase
from primesense import openni2
import time

class deriveDeviceListener(openni2.DeviceListener):
    
    checkDis = False
    checkCon = False
    
    def on_connected(self, devinfo):
        openni2.DeviceListener.on_connected(self, devinfo)
        self.checkDis = True

    
    def on_disconnected(self, devinfo):
        openni2.DeviceListener.on_disconnected(self, devinfo)
        self.checkCon = True
    


class Test_enumeration(CrayolaTestBase):
    
    def test_enum(self):
        try:
            openni2.Device.open_all()
        except openni2.OpenNIError as ex:
            assert ex is not None, "could not open all devices"
        devListener = deriveDeviceListener()
        for device in self.devices:
            device.set_usb_iso()
            device.hard_reset()
            assert devListener.checkDis is True, "No callback form disconnected"
            time.sleep(15)
            assert  devListener.checkCon is True, "No callback from connected"
             
             
    