__Debug__ = True

___FramesInfoDebug___ = True

from NIBaseTest import *
import ConfigParser
import NIps
from NIps import *
from NITest_GeneralReadFrameCorrectness import *
config = ConfigParser.ConfigParser()
#config.read("Pastel-Config.ini")
import random
import NIGris
reload(NIGris)

class NITest_Permutations(NIBaseTest):
    """General Permutations Test, Can recive any fitted test class as a subject for the test"""
    def __init__(self,**kwargs):
        """ num_frames = number of frames, capture_mode = True - for capture mode"""
        NIBaseTest.__init__(self)
        self.num_frames = kwargs.get("num_frames",20)
        self.usb_mode = kwargs.get("usb_mode",0)
        self.num_times = kwargs.get("num_times",1)
        self.log_sdk_on_fail_only = kwargs.get("log_sdk_on_fail_only",False)
        if self.usb_mode == 0:
            usb_string = "ISO"
        else:
            usb_string = "BULK"
            
        self.html_path = kwargs.get("html_path",'./Results/NITest_Permutations-'+usb_string+'.html')
        self.html_log.start_log(self.html_path,'NITest_Permutations-'+usb_string)

    def run(self):
        
        # Generate Streams combination

        #params_list = self.generate_param_permutations()
        #Depth[640,480,60,3,1];Image[640,480,60,5,5]
        
        params_list = []
        params_list.append(SensorParams(streams = ['depth','IR'], depth_xres = 320,depth_yres =240 , depth_fps = 30,IR_xres = 640,IR_yres =480, IR_fps = 30))
        params_list.append(SensorParams(streams = ['depth','IR'], depth_xres = 160,depth_yres =120 , depth_fps = 30,IR_xres = 640,IR_yres =480, IR_fps = 30))
        params_list.append(SensorParams(streams = ['depth'], depth_xres = 320,depth_yres =240 , depth_fps = 30))
        params_list.append(SensorParams(streams = ['depth'], depth_xres = 160,depth_yres =120 , depth_fps = 30))
        params_list.append(SensorParams(streams = ['IR'], IR_xres = 640,IR_yres =480, IR_fps = 30))

        #for i in range(500):
        #if (self.usb_mode == 2): #BULK
        #    params_list = self.generate_param_permutations(False)
        #else:
        #    params_list = self.generate_param_permutations(True)
        

        for index,specific_comb in enumerate(params_list):
            print index,'of',len(params_list)
            print 'Testing', specific_comb.open_string()
            

            for i in range(self.num_times):
                temp_result = ''
                # Open Sensor for the combination
                extra_string = ('Combination %s of %s\n' % (index+1,len(params_list)))
                rc = self._open_sensor(specific_comb,self.usb_mode,True,extra_string)

                if rc:
                    
                    # Run the GRFK test

                    Test = NITest_GeneralReadFrameCorrectness(self.num_frames,self.ni_device)
                    Test.run(specific_comb)

                    # Close sensor and get the SDK log results
                    sdk_log = self._close_sensor()

                    # Check that the GRFK passed
                    if Test.test_result.result:
                        self.test_result.result+=1
                        temp_result += "Stream Combination " + specific_comb.open_string() + " Failed\n"
                        passed = False
                    else:
                        temp_result += "Stream Combination " + specific_comb.open_string() + " Passed\n"
                        passed = True

                    
                    temp_result += Test.test_result.string
                    self.test_result.string += Test.test_result.string
                    
                    if (passed == True) and (self.log_sdk_on_fail_only == True):
                        sdk_log = ''
                    
                    temp_result = ('Combination %s of %s\n' % (index+1,len(params_list))) + temp_result
                    
                    self.html_log.add(passed,temp_result,sdk_log)
                        
                    if not passed and ___FramesInfoDebug___ == True:
                        self.html_log.add(passed,"Extra Frame Info",Test.frames_info)


    def generate_param_permutations(self,single_audio_permutations = True):
        
        params_list = []
        
        res_list = ['vga' , 'qvga']
        
        
        fps_list = [30 ,60, 25]
        
        
        sample_rate_list = [8000, 11025, 12000,16000, 22050, 24000,32000, 44100, 48000]
        audio_channel_list = [1,2]
        
        conf_list = []
        for res in res_list:
           for fps in fps_list:
               conf_list.append([res, fps])
        
        # input formats (depth 0 16 bit uncompressed is removed, image 2 jpeg is removed)
        depth_inputformat_list = [1,3]
        image_inputformat_list = [1,5]
        # output formats
        depth_outputformat_list = [0, 1]
        image_outputformat_list = [4, 5]
        ir_outputformat_list    = [3, 5]

        
        
        # --------------------- ONE STREAM --------------------- #
        
        # depth
        for depth in conf_list:
            for d_inputformat in depth_inputformat_list:
                for d_outputformat in depth_outputformat_list:
                    params_list.append(SensorParams(streams = ['depth'], depth_res = depth[0],depth_fps = depth[1],
                                                    depth_inputformat = d_inputformat, depth_outputformat = d_outputformat ))
        
        # image
        for image in conf_list:
            for i_inputformat in image_inputformat_list:
                for i_outputformat in image_outputformat_list:
                    params_list.append(SensorParams(streams = ['image'], image_res = image[0],image_fps = image[1],
                                                    image_inputformat = i_inputformat, image_outputformat = i_outputformat))
           
        # IR                            
        for IR in conf_list:
            for ir_outputformat in ir_outputformat_list:
                params_list.append(SensorParams(streams = ['IR'], IR_res = IR[0],IR_fps = IR[1],
                                                ir_outputformat = ir_outputformat))
        
        # audio            
        if single_audio_permutations == True:
            for sample_rate in sample_rate_list:
                for  audio_channel in  audio_channel_list:
                    params_list.append(SensorParams(streams = ['audio'],audio_samplerate = sample_rate, audio_channels = audio_channel))        
            
        # --------------------- TWO STREAMS --------------------- #
           
        # depth image
        for depth in conf_list:
            for image in conf_list:
                for d_inputformat in random.sample(depth_inputformat_list,1):
                        for d_outputformat in random.sample(depth_outputformat_list,1):
                            for i_inputformat in random.sample(image_inputformat_list,1):
                                for i_outputformat in random.sample(image_outputformat_list,1):
                                    params_list.append(SensorParams(streams = ['depth','image'], depth_res = depth[0],depth_fps = depth[1],image_res = image[0],image_fps = image[1],
                                                                    depth_inputformat = d_inputformat, depth_outputformat = d_outputformat,
                                                                    image_inputformat = i_inputformat, image_outputformat = i_outputformat))
        
        # depth IR
        for depth in conf_list:
            for IR in conf_list:
                for d_inputformat in depth_inputformat_list:
                        for d_outputformat in depth_outputformat_list:
                            for ir_outputformat in ir_outputformat_list:
                                    params_list.append(SensorParams(streams = ['depth','IR'], depth_res = depth[0],depth_fps = depth[1],IR_res = IR[0],IR_fps = IR[1],
                                                                    depth_inputformat = d_inputformat, depth_outputformat = d_outputformat,
                                                                    ir_outputformat = ir_outputformat))
    
        # depth audio
        for depth in conf_list:
            for d_inputformat in depth_inputformat_list:
                    for d_outputformat in depth_outputformat_list:
                        #for sample_rate in sample_rate_list:
                            #for  audio_channel in  audio_channel_list:
                                params_list.append(SensorParams(streams = ['depth','audio'], depth_res = depth[0],depth_fps = depth[1],
                                                                depth_inputformat = d_inputformat, depth_outputformat = d_outputformat,
                                                                audio_samplerate = 48000, audio_channels = 2))
    
        ## image IR
        #for image in conf_list:
        #    for IR in conf_list:
        #        for i_inputformat in image_inputformat_list:
        #            for i_outputformat in image_outputformat_list:
        #                    for ir_outputformat in ir_outputformat_list:
        #                            params_list.append(SensorParams(streams = ['image','IR'], image_res = image[0],image_fps = image[1],IR_res = IR[0],IR_fps = IR[1],
        #                                                            image_inputformat = i_inputformat, image_outputformat = i_outputformat,
        #                                                            ir_outputformat = ir_outputformat))
    
        # image audio
        for image in conf_list:
            for i_inputformat in image_inputformat_list:
                    for i_outputformat in image_outputformat_list:
                        #for sample_rate in sample_rate_list:
                            #for  audio_channel in  audio_channel_list:
                                params_list.append(SensorParams(streams = ['image','audio'], image_res = image[0],image_fps = image[1],
                                                                image_inputformat = i_inputformat, image_outputformat = i_outputformat,
                                                                audio_samplerate = 48000, audio_channels = 2))
     
        # IR audio
        for IR in conf_list:
            for ir_outputformat in ir_outputformat_list:
                    #for sample_rate in sample_rate_list:
                        #for  audio_channel in  audio_channel_list:
                                params_list.append(SensorParams(streams = ['IR','audio'], IR_res = IR[0],IR_fps = IR[1],
                                                                ir_outputformat = ir_outputformat,
                                                                audio_samplerate = 48000, audio_channels = 2))             
        
        # --------------------- THREE STREAMS --------------------- #
        
        ## depth image IR
        #for depth in conf_list:
        #    for image in conf_list:
        #        for IR in conf_list:
        #            for d_inputformat in depth_inputformat_list:
        #                for d_outputformat in depth_outputformat_list:
        #                    for i_inputformat in image_inputformat_list:
        #                        for i_outputformat in image_outputformat_list:
        #                            for ir_outputformat in ir_outputformat_list:
        #                                params_list.append(SensorParams(streams = ['depth','image','IR'], depth_res = depth[0],depth_fps = depth[1],image_res = image[0],image_fps = image[1],IR_res = IR[0],IR_fps = IR[1],
        #                                                                depth_inputformat = d_inputformat, depth_outputformat = d_outputformat,
        #                                                                image_inputformat = i_inputformat, image_outputformat = i_outputformat,
        #                                                                ir_outputformat = ir_outputformat))
    
        # depth image audio
        for depth in conf_list:
            for image in conf_list:
                    for d_inputformat in depth_inputformat_list:
                        for d_outputformat in depth_outputformat_list:
                            for i_inputformat in image_inputformat_list:
                                for i_outputformat in image_outputformat_list:
                                    #for sample_rate in sample_rate_list:
                                        #for  audio_channel in  audio_channel_list:
                                            params_list.append(SensorParams(streams = ['depth','image','audio'], depth_res = depth[0],depth_fps = depth[1],image_res = image[0],image_fps = image[1],
                                                                            depth_inputformat = d_inputformat, depth_outputformat = d_outputformat,
                                                                            image_inputformat = i_inputformat, image_outputformat = i_outputformat,
                                                                            audio_samplerate = 48000, audio_channels = 2))  
    
        # depth IR audio
        #for depth in conf_list:
            for IR in conf_list:
                for d_inputformat in depth_inputformat_list:
                    for d_outputformat in depth_outputformat_list:
                            for ir_outputformat in ir_outputformat_list:
                                #for sample_rate in sample_rate_list:
                                    #for  audio_channel in  audio_channel_list:
                                        params_list.append(SensorParams(streams = ['depth','IR','audio'], depth_res = depth[0],depth_fps = depth[1],IR_res = IR[0],IR_fps = IR[1],
                                                                        depth_inputformat = d_inputformat, depth_outputformat = d_outputformat,     
                                                                        ir_outputformat = ir_outputformat,
                                                                        audio_samplerate = 48000, audio_channels = 2))
    
        ## image IR audio
        #for image in conf_list:
        #    for IR in conf_list:
        #        for i_inputformat in image_inputformat_list:
        #            for i_outputformat in image_outputformat_list:
        #                for ir_outputformat in ir_outputformat_list:
        #                    #for sample_rate in sample_rate_list:
        #                        #for  audio_channel in  audio_channel_list:
        #                            params_list.append(SensorParams(streams = ['image','IR','audio'],image_res = image[0],image_fps = image[1],IR_res = IR[0],IR_fps = IR[1],  
        #                                                            image_inputformat = i_inputformat, image_outputformat = i_outputformat,
        #                                                            ir_outputformat = ir_outputformat,
        #                                                            audio_samplerate = 48000, audio_channels = 2))
            
        # --------------------- FOUR STREAMS --------------------- #
        #for depth in conf_list:
        #    for image in conf_list:
        #        for IR in conf_list:
        #            for d_inputformat in depth_inputformat_list:
        #                for d_outputformat in depth_outputformat_list:
        #                    for i_inputformat in image_inputformat_list:
        #                        for i_outputformat in image_outputformat_list:
        #                            for ir_outputformat in ir_outputformat_list:
        #                                #for sample_rate in sample_rate_list:
        #                                    #for  audio_channel in  audio_channel_list:
        #                                        params_list.append(SensorParams(streams = ['depth','image','IR','audio'], depth_res = depth[0],depth_fps = depth[1],image_res = image[0],image_fps = image[1],IR_res = IR[0],IR_fps = IR[1],
        #                                                                        depth_inputformat = d_inputformat, depth_outputformat = d_outputformat,
        #                                                                        image_inputformat = i_inputformat, image_outputformat = i_outputformat,
        #                                                                        ir_outputformat = ir_outputformat,
        #                                                                        audio_samplerate = 48000, audio_channels = 2))
        
        
        # image IR (Image and IR are not suppose to work together hence, we put only selected Image/IR combinations)
        for image in conf_list:
            for IR in conf_list:
                params_list.append(SensorParams(streams = ['image','IR'], image_res = image[0],image_fps = image[1],IR_res = IR[0],IR_fps = IR[1]))
            
            
            
        ####no_audio_params_list = []
        ####for sp in params_list:
        ####    if 'audio' not in sp.streams:
        ####        no_audio_params_list.append(sp)
                
        
        return params_list

if __name__ == "__main__":
    
    print "Permutation Test."
    
    test = NITest_Permutations(num_times = 50,num_frames = 100,capture_mode = False,usb_mode = 0, log_sdk_on_fail_only = False)
    #try:
    test.run()
    #except BaseException, exp:
    #    print exp
    #    raw_input("Press ENTER to exit")
    print test.test_result.result
    


