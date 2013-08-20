
from crayola import CrayolaTestBase
from primesense import openni2

class TestMultipleStream(CrayolaTestBase):
    
    def _test_single_operation(self, stream):
        stream.start()
        self.verify_stream_fps(stream, 2)
        stream.stop()
    
    def _test_simultaneus(self, stream1, stream2, stream3):
        stream1.start()
        stream2.start()
        stream3.start()
        self.verify_stream_fps(stream1, 2)
        self.verify_stream_fps(stream2, 2)
        self.verify_stream_fps(stream3, 2)
        stream1.stop()
        stream2.stop()
        stream3.stop()
    
    def _test_conflict(self, stream1, stream2, videoMode):
        stream1.start() 
        try:
            stream2.set_video_mode(videoMode)
        except openni2.OpenNIError as ex:   
                assert ex is not None, "Conflict: can set video mode to disconnected stream "
        stream1.stop()
    
    def _test_IR_sensor(self, device):
        try:
            stream1 = openni2.Device.create_ir_stream(device)
            stream2 = openni2.Device.create_ir_stream(device)
            stream3 = openni2.Device.create_ir_stream(device)
        except openni2.OpenNIError as ex:
            self.logger.warn("Can't open %s at  %s", self.device.get_ir_stream, ex)
        if not stream1 or stream2 or stream3:
            self.logger.warn("Can't open %s", self.device.get_ir_stream)
        with stream1 and stream2 and stream3:
            self._test_single_operation(stream1)
            self._test_single_operation(stream2)
            self._test_single_operation(stream3)
            self._test_simultaneus(stream1, stream2, stream3)
            sensorInfo = self.device.get_sensor_info(openni2.SENSOR_IR)
            if sensorInfo is None:
                return
            videoModes = sensorInfo.videoModes
            for mode in videoModes:
                self._test_conflict(stream1, stream2, mode)
            stream1.close()
            stream2.close()
            stream3.close()
    
    def _test_depth_sensor(self, device):
        try:
            stream1 = openni2.Device.create_depth_stream(device)
            stream2 = openni2.Device.create_depth_stream(device)
            stream3 = openni2.Device.create_depth_stream(device)
        except openni2.OpenNIError as ex:
            self.logger.warn("Can't open %s at  %s", self.device.get_depth_stream, ex)
        if not stream1 or stream2 or stream3:
            self.logger.warn("Can't open %s", self.device.get_depth_stream)
        with stream1 and stream2 and stream3:
            self._test_single_operation(stream1)
            self._test_single_operation(stream2)
            self._test_single_operation(stream3)
            self._test_simultaneus(stream1, stream2, stream3)
            sensorInfo = self.device.get_sensor_info(openni2.SENSOR_DEPTH)
            if sensorInfo is None:
                return
            videoModes = sensorInfo.videoModes
            for mode in videoModes:
                self._test_conflict(stream1, stream2, mode)
            stream1.close()
            stream2.close()
            stream3.close()       
        
    def _test_color_sensor(self, device):
        try:
            stream1 = openni2.Device.create_color_stream(device)
            stream2 = openni2.Device.create_color_stream(device)
            stream3 = openni2.Device.create_color_stream(device)
        except openni2.OpenNIError as ex:
            self.logger.warn("Can't open %s at  %s", self.device.get_color_stream, ex)
        if not stream1 or stream2 or stream3:
            self.logger.warn("Can't open %s", self.device.get_color_stream)
        with stream1 and stream2 and stream3:
            self._test_single_operation(stream1)
            self._test_single_operation(stream2)
            self._test_single_operation(stream3)
            self._test_simultaneus(stream1, stream2, stream3)
            sensorInfo = self.device.get_sensor_info(openni2.SENSOR_COLOR)
            if sensorInfo is None:
                return
            videoModes = sensorInfo.videoModes
            for mode in videoModes:
                self._test_conflict(stream1, stream2, mode)
            stream1.close()
            stream2.close()
            stream3.close()       

    
    def test_multiple_stream(self):
        for device in self.devices:
            self.device.set_usb_iso()
            self._test_IR_sensor(device)
            self._test_color_sensor(device)
            self._test_depth_sensor(device)
    
        
        
