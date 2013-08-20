
from crayola import CrayolaTestBase
from primesense import openni2, _openni2
import primesense
import time

class testSyncFrame(CrayolaTestBase): 

    def _reg_flow(self, device, dStream, cStream):
        with dStream and cStream:
            cStream.start()
            dStream.start()
            device.set_depth_color_sync_enabled(True)
            time.sleep(3)
            for _ in range(50):
                readStream = openni2.wait_for_any_stream([dStream, cStream], 1)  
                if readStream is  dStream:
                    assert openni2.wait_for_any_stream([cStream], 0) is not None, "didn't read the second(color) frame"
                elif readStream is cStream:
                    assert openni2.wait_for_any_stream([dStream], 0) is not None, "didn't read the second(depth) frame"
                else:
                    assert False, "Didn't read any frame"
            device.set_depth_color_sync_enabled(False)
        
    def _app_delay (self, device, firstStream, secondStream):
        with firstStream and secondStream:
            firstStream.start()
            secondStream.start()
            device.set_depth_color_sync_enabled(True)
            time.sleep(3)
            for _ in range(50): 
                assert openni2.wait_for_any_stream([firstStream], 1) is not None, "didn't read first frame"
                time.sleep(0.5)
                assert openni2.wait_for_any_stream([secondStream], 0) is not None, "didn't read the second frame"
                tsFirstFrame = firstStream.read_frame().timestamp
                tsSecondFrame =  secondStream.read_frame().timestamp
                assert - 3000 < tsSecondFrame -  tsFirstFrame and tsSecondFrame -  tsFirstFrame < 3000 ," time stamp bigger than 3ms"
            device.set_depth_color_sync_enabled(False)
    
    def _skip_frame(self, device, firstStream, secondStream):
        with firstStream and secondStream:
            firstStream.start()
            secondStream.start()  
            device.set_depth_color_sync_enabled(True)
            time.sleep(3)
            for _ in range(50):
                assert openni2.wait_for_any_stream([firstStream], 1) is not None, "didn't read first frame"
                assert openni2.wait_for_any_stream([firstStream], 1) is not None, "didn't read second frame"
                assert openni2.wait_for_any_stream([secondStream], 0) is not None, "didn't read the third frame"
                firstFrame = firstStream.read_frame()
                thirdFrame = secondStream.read_frame()
                tsFirst = firstFrame.timestamp
                tsThird = thirdFrame.timestamp
                assert -3000 < tsThird - tsFirst and tsThird - tsFirst < 3000, "time stamp don't match"
            device.set_depth_color_sync_enabled(False)

    def _event_base(self, device, firstStream, secondStream):   
        timeRegistersFirst = []
        timeRgistersSecond = []
        winTimestampFirst = []
        winTimestampSecond = []
        i = [0] 
        j = [0]
        
        def callback1(stream):
            if j[0] < 50:
                timeRegistersFirst.append(stream.read_frame().timestamp)
                winTimestampFirst.append(time.time())
                j[0] += 1
            
        def callback2(stream):
            if i[0] < 50:
                timeRgistersSecond.append(stream.read_frame().timestamp)
                winTimestampSecond.append(time.time())
                i[0] += 1
        
        firstStream.start()
        secondStream.start()
        device.set_depth_color_sync_enabled(True)
        time.sleep(3)
        firstStream.register_new_frame_listener(callback1)
        secondStream.register_new_frame_listener(callback2)
        time.sleep(2)
        firstStream.unregister_new_frame_listener(callback1)
        secondStream.unregister_new_frame_listener(callback2)
        assert len(timeRegistersFirst) is 50 or len(timeRgistersSecond) is 50," didn't read all the wanted frames"
        for x in range(50):
            assert -3000 < timeRgistersSecond[x] - timeRegistersFirst[x] and timeRgistersSecond[x] - timeRegistersFirst[x] < 3000, "time stamp don't match"
            assert -3000 < winTimestampSecond[x] - winTimestampFirst[x] and winTimestampSecond[x] - winTimestampFirst[x] < 3000, "windows time stamp don't match"
        device.set_depth_color_sync_enabled(False)    

    def test_sync_reg(self):
        for device in self.devices:
            if(device.device_info.name == "PS1080"):
                dStream = openni2.Device.create_depth_stream(device)
                cStream = openni2.Device.create_color_stream(device)
                try:
                    self._reg_flow(device, dStream, cStream)
                finally:
                    dStream.close()
                    cStream.close()

    def test_sync_delay(self):
        for device in self.devices:
            if(device.device_info.name == "PS1080"):
                try:
                    dStream = openni2.Device.create_depth_stream(device)
                    cStream = openni2.Device.create_color_stream(device)
                    self._app_delay(device, dStream, cStream)
                    dStream = openni2.Device.create_depth_stream(device)
                    cStream = openni2.Device.create_color_stream(device)
                    self._app_delay(device, cStream, dStream)
                finally:
                    dStream.close()
                    cStream.close()                    
                    
    def test_sync_skip(self):
        for device in self.devices:
            if(device.device_info.name == "PS1080"):
                try:
                    firstDStream = openni2.Device.create_depth_stream(device) 
                    cStream = openni2.Device.create_color_stream(device)
                    self._skip_frame(device, firstDStream, cStream)
                finally:
                    firstDStream.close()
                    cStream.close()
                try:
                    firstCStream = openni2.Device.create_color_stream(device)
                    dStream = openni2.Device.create_depth_stream(device)
                    self._skip_frame(device, firstCStream, dStream)
                finally: 
                    firstCStream.close()
                    dStream.close()
                    
    def test_sync_event(self):
        for device in self.devices:
            if(device.device_info.name == "PS1080"):
                try:
                    dStream = openni2.Device.create_depth_stream(device)
                    cStream = openni2.Device.create_color_stream(device)
                    self._event_base(device, dStream, cStream)
                finally:
                    dStream.close()
                    cStream.close()

                    
