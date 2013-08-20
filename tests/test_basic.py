

from crayola import CrayolaTestBase
from primesense import openni2


class TestBase(CrayolaTestBase):
    def test_base(self):
        self.device.set_usb_iso() 
        try:
            stream = openni2.Device.create_depth_stream(self.device)
            stream.start()
        except openni2.OpenNIError as ex:
            self.logger.warn("Can't open %s at  %s", self.device.get_depth_stream, ex)
        if not stream:
            self.logger.warn("Can't open %s", self.device.get_depth_stream) 
        with stream:
            self.verify_stream_fps(stream, 2)
        stream.close()