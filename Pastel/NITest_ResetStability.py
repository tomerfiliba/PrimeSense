import array
from progressbar import *
import time
from ctypes import *
from NIBaseTest import SensorParams
from NITest_GeneralReadFrameCorrectness import NITest_GeneralReadFrameCorrectness
__Debug__ = False
from NIBaseTest import *
import ConfigParser
from NIps import *

config = ConfigParser.ConfigParser()
config.read("./NITest_ResetStability.ini")

class NITest_ResetStability (NIBaseTest):

    def __init__(self, ** kwargs):
        # initialization
        NIBaseTest.__init__(self)
        self.html_path = kwargs.get("html_path", './Results/NITest_ResetStability.html')
        self.html_log.start_log(self.html_path, 'NITest_ResetStability')
        self.config = {}
        self.read_frames = kwargs.get("read_frames", False)
        ini_section = kwargs.get("INISection", "NITest_ResetStability")
        self.config["NumSoftResets"] = int(kwargs.get("NumSoftResets",config.get(ini_section,"NumSoftResets")))
        self.config["NumHardResets"] = int(kwargs.get("NumHardResets",config.get(ini_section,"NumHardResets")))
        self.config["SleepBetweenHardResets"] = int(kwargs.get("SleepBetweenHardResets",config.get(ini_section,"SleepBetweenHardResets")))

    def run(self, sp=SensorParams()):
        
        
        widgets = [Bar('>'), ' ', ETA(), ' ', ReverseBar('<')]
        sdk = ''
        self.test_result.result = 0

        break_occured = False

        # open sensor
        sensor_params = SensorParams(streams = ['depth','IR'], depth_xres = 320,depth_yres = 240, depth_fps = 30,IR_xres = 640,IR_yres = 480, IR_fps = 30)

        print "Depth resolution: %sX%s, fps: %s" % (sensor_params.depth_xres, sensor_params.depth_yres, sensor_params.depth_fps)

        print 'Performing soft resets'
        
        for i in range(1,1+self.config["NumSoftResets"]):
            temp_result = ''
            # Open Sensor for the combination
            rc = self._open_sensor(sensor_params,1,True,"")

            if len(self.ni_device.device_nodes) == 0:
                return;
            # Soft Reset
            rc = niSetIntProperty(self.ni_device.device_nodes[0], "SoftReset" ,1 )
            
            # Close sensor and get the SDK log results
            sdk_log = self._close_sensor()

            # Open Sensor again for the combination
            rc = self._open_sensor(sensor_params,1,True,"")


            # Run the GRFK test

            Test = NITest_GeneralReadFrameCorrectness(120,self.ni_device)
            Test.run(sensor_params)

            # Close sensor and get the SDK log results
            sdk_log = self._close_sensor()

            # Check that the GRFK passed
            if Test.test_result.result:
                self.test_result.result+=1
                temp_result += "Soft reset number %d failed\n" % i
                passed = False
            else:
                temp_result += "Soft reset number %d passed\n" % i
                passed = True

            
            temp_result += Test.test_result.string
            self.test_result.string += Test.test_result.string
            
            
            # temp_result = ('Combination %s of %s\n' % (index+1,len(params_list))) + temp_result
            
            self.html_log.add(passed,temp_result,sdk_log)
                
            # if not passed and ___FramesInfoDebug___ == True:
            #     self.html_log.add(passed,"Extra Frame Info",Test.frames_info)
        



if __name__ == "__main__":
    test = NITest_ResetStability(read_frames = True,NumSoftResets=50,NumHardResets = 0)
    test.run()
    