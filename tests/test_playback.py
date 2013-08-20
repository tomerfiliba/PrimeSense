from crayola import CrayolaTestBase
from primesense import openni2
import random
from primesense.openni2 import wait_for_any_stream, VideoMode
import time

class TestPlayback(CrayolaTestBase):
    
    def test_seek(self):
        for device in self.devices:     
            for sensorType in [openni2.SENSOR_DEPTH, openni2.SENSOR_COLOR, openni2.SENSOR_IR]:   
                stream = device.create_stream(sensorType)
                stream.start()
                with stream:
                    recorder = openni2.Recorder("playback_seek.ONI")
                    recorder.attach(stream, True)                
                    recorder.start()
                    with recorder:
                         for i in range(50):
                             result = wait_for_any_stream([stream], 1)
                             assert result is not  None, "can't read frame"
                             frame = stream.read_frame()
                fileDev = openni2.Device.open_file("playback_seek.ONI")
                with fileDev:
                    assert fileDev.is_file() is True, "device is not a file"
                    streamFromFile = fileDev.create_stream(sensorType)
                    streamFromFile.start() 
                    index = random.randint(0,50)
                    fileDev.playback.seek(streamFromFile, index)
                    assert streamFromFile.read_frame().frameIndex == index, "seek won't work properly"
                    streamFromFile.stop()
                    streamFromFile.close()            
    
    def test_repeat(self):
        for device in self.devices:   
            for sensorType in [openni2.SENSOR_DEPTH, openni2.SENSOR_IR, openni2.SENSOR_COLOR]:
                stream = device.create_stream(sensorType)
                stream.start()
                with stream:
                    recorder = openni2.Recorder("playback_repeat.ONI")
                    recorder.attach(stream, True)                
                    recorder.start()
                    with recorder:
                         for i in range(50):
                             result = wait_for_any_stream([stream], 1)
                             assert result is not  None, "can't read frame"
                             frame = stream.read_frame()
                fileDev = openni2.Device.open_file("playback_repeat.ONI")
                with fileDev:
                    assert fileDev.is_file() is True, "device is not a file"
                    streamFromFile = fileDev.create_stream(sensorType)
                    streamFromFile.start()
                    fileDev.playback.set_repeat_enabled(True)
                    for _ in range(50):
                        streamFromFile.read_frame()
                    index =  streamFromFile.read_frame().frameIndex
                    assert index == 1, "repeat won't work"
                    streamFromFile.stop()
                    streamFromFile.close()

                