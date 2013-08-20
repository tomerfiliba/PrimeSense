
from crayola import CrayolaTestBase
from primesense import openni2
from multiprocessing.dummy import Process
from nose.tools import with_setup
from rpyc.core.stream import Stream
import time
import copy

class TestSwitchMode(CrayolaTestBase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
                 
    def check_frames(self, device, sensorType, videoMode):
        stream = device.create_stream(sensorType)
        stream.set_video_mode(videoMode)
        stream.start()
        self.verify_stream_fps(stream, 2)
        stream.stop()
        stream.close()
      
    def get_all_permutations(self):
        perList = []
        for device in self.devices:
            for sensorType in [openni2.SENSOR_DEPTH, openni2.SENSOR_COLOR, openni2.SENSOR_IR]:
                sensorInfo = device.get_sensor_info(sensorType)
                if not sensorInfo is None:
                    videoModes = sensorInfo.videoModes
                    for videoMode in videoModes:
                        perList.append([device,sensorType, copy.deepcopy(videoMode)])
        return perList

    def test_switching_mode(self):
        CrayolaTestBase.setUp(self)
        permutations = self.get_all_permutations()
        for perm in permutations:
            if  perm[2].resolutionY == 720:
                pass
            else:
                yield self.check_frames, perm[0], perm[1], perm[2]
        CrayolaTestBase.tearDown(self)
			