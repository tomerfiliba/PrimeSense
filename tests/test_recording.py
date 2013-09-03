import glob
import copy
from crayola import CrayolaTestBase
from primesense import openni2
from primesense.openni2 import wait_for_any_stream

class TestRecording(CrayolaTestBase):
    
    def _record_to_file(self, indexOfDevice, sensorType, videoMode, allow_lossy_compression):
        device = self.devices[indexOfDevice]
        stream = device.create_stream(sensorType)
        with stream:
            stream.set_video_mode(videoMode)
            recorder = openni2.Recorder("test_record.ONI")
            with recorder:
                recorder.attach(stream, allow_lossy_compression)
                recorder.start()
                stream.start()
                for i in range(50):
                    result = wait_for_any_stream([stream], 1)
                    assert result is not  None, "can't read frame"
                    frame = stream.read_frame()
                    assert frame is not None, " didn't read frame properly"
        fileDev = openni2.Device.open_file("test_record.ONI")
        assert fileDev.is_file() is True, "device is not a file"
        streamFromFile = fileDev.create_stream(sensorType)
        streamFromFile.start() 
        numberOfFrames = fileDev.playback.get_number_of_frames(streamFromFile)
        
        assert numberOfFrames <= 50, "Too many frames in test"
        assert numberOfFrames >= 50, "Too few frames"
        for x in range(50):
            result = wait_for_any_stream([streamFromFile], 1)
            assert result is not  None, "can't read frame from file"
            frame = streamFromFile.read_frame()
            assert frame is not None, "didn't read frame from file properly"
        streamFromFile.stop()
        streamFromFile.close()
  
    def get_all_permutations(self):
        perList = []
        i = 0
        for device in self.devices:
            for sensorType in [openni2.SENSOR_DEPTH, openni2.SENSOR_COLOR, openni2.SENSOR_IR]:
                sensorInfo = device.get_sensor_info(sensorType)
                if not sensorInfo is None:
                    videoModes = sensorInfo.videoModes
                    for videoMode in videoModes:
                        perList.append([i, copy.deepcopy(sensorType), copy.deepcopy(videoMode)])
            i+=1
        return perList
    
    def _open_old_files(self):
        try:
            for file in glob.glob("checkFiles/*.ONI"):
                fileDev = openni2.Device.open_file(file)
                for sensorType in [openni2.SENSOR_DEPTH, openni2.SENSOR_COLOR, openni2.SENSOR_IR]:
                    try:
                        stream = fileDev.create_stream(sensorType)
                    except openni2.OpenNIError as ex:
                        continue
                    stream.start()
                    numOfFrames = fileDev.playback.get_number_of_frames(stream)
                    for x in range (numOfFrames):
                        result = wait_for_any_stream([stream], 1)
                        assert result is not  None, "can't read frame from file"
                        frame = stream.read_frame()
                        assert frame is not None,"can't read frame"
        except openni2.OpenNIError as ex:
            print ex
            self.logger.warn("couldn't open and playback file")
    
    def test_record(self):
        CrayolaTestBase.setUp(self)
        permutations = self.get_all_permutations()
        CrayolaTestBase.tearDown(self)
        for perm in permutations:
            if perm[2].resolutionY == 720:
                pass
            else:
                yield self._record_to_file, perm[0], perm[1], perm [2], True
                yield self._record_to_file, perm[0], perm[1], perm [2], False
        
    def test_open_old_file(self):
        #CrayolaTestBase.setUp(self)
        self._open_old_files()
        #CrayolaTestBase.tearDown(self)
        