__Debug__ = False
___FramesInfoDebug___ = True
from NIBaseTest import *
from NIps import *
import os
import ConfigParser
import NIps
import ctypes
import math

config = ConfigParser.ConfigParser()
config.read("./NITest_GeneralReadFrameCorrectness.ini")


class NITest_GeneralReadFrameCorrectness():
    def __init__(self,num_frames = 5,ni_device = None,**kwargs):
        #BaseTest.__init__(self)
        self.test_result = TestResult()
        self.ni_device = ni_device
        self.num_frames = num_frames
        self.bad_timestamp_frames = {}
        self.bad_timestamp_precent = {}
        self.bad_average_frames = {}
        self.bad_average_precent = {}
        self.bad_framesync_frames = 0
        self.bad_framesync_precent = 0
        self.bad_frameID_frames = 0
        self.bad_frameID_precent = 0
        self.test_result.result = 0
        self.config = {}
        ini_section = kwargs.get("INISection","NITest_GeneralReadFrameCorrectness")
        self.config["TimeStampThresholdHigh30"] = int(kwargs.get("TimeStampThresholdHigh30",config.get(ini_section,"TimeStampThresholdHigh30")))
        self.config["TimeStampThresholdHigh60"] = int(kwargs.get("TimeStampThresholdHigh60",config.get(ini_section,"TimeStampThresholdHigh60")))
        self.config["TimeStampThresholdHigh25"] = int(kwargs.get("TimeStampThresholdHigh25",config.get(ini_section,"TimeStampThresholdHigh25")))
        self.config["TimeStampThresholdHigh10"] = int(kwargs.get("TimeStampThresholdHigh10",config.get(ini_section,"TimeStampThresholdHigh10")))
        self.config["TimeStampThresholdLow30"] = int(kwargs.get("TimeStampThresholdLow30",config.get(ini_section,"TimeStampThresholdLow30")))
        self.config["TimeStampThresholdLow60"] = int(kwargs.get("TimeStampThresholdLow60",config.get(ini_section,"TimeStampThresholdLow60")))
        self.config["TimeStampThresholdLow25"] = int(kwargs.get("TimeStampThresholdLow25",config.get(ini_section,"TimeStampThresholdLow25")))
        self.config["TimeStampThresholdLow10"] = int(kwargs.get("TimeStampThresholdLow10",config.get(ini_section,"TimeStampThresholdLow10")))
        self.config["BadTimeStampFramesPrecent_IR"] = int(kwargs.get("BadTimeStampFramesPrecent_IR",config.get(ini_section,"BadTimeStampFramesPrecent_IR")))
        self.config["BadTimeStampFramesPrecent_Depth"] = int(kwargs.get("BadTimeStampFramesPrecent_Depth",config.get(ini_section,"BadTimeStampFramesPrecent_Depth")))
        self.config["BadTimeStampFramesPrecent_Image"] = int(kwargs.get("BadTimeStampFramesPrecent_Image",config.get(ini_section,"BadTimeStampFramesPrecent_Image")))
        self.config["BadTimeStampFramesPrecent_Audio"] = int(kwargs.get("BadTimeStampFramesPrecent_Audio",config.get(ini_section,"BadTimeStampFramesPrecent_Audio")))
        self.config["BadAverageFramesPrecent"] = int(kwargs.get("BadAverageFramesPrecent",config.get(ini_section,"BadAverageFramesPrecent")))
        self.config["TimeStampThresholdAudio"] = float(kwargs.get("TimeStampThresholdAudio",config.get(ini_section,"TimeStampThresholdAudio")))

        if ___FramesInfoDebug___ == True:
            self.frames_info = ''

    def run(self,sensor_params = None):



        if self.ni_device == None:
            self.test_result.result = 1
            self.test_result.string = "Bad Test - Tried to run GRFC with closed sensor\n"
            return

        # Variables
        TimeStamp = [0]
        FrameID = [0]
        framesync = [0]
        buffer_size = [0]
        StreamBufAddr = {}
        StreamBufSize = {}
        StreamFPS = {}
        CurTimeStampList = {}
        PrevTimeStampList = {}
        DifTimeStampList = {}
        CurFrameIDList = {}
        PrevFrameIDList = {}
        map_mode = NiMapOutputMode()
        wave_mode = NiWaveOutputMode()

        # Get Primary Stream and framesync conditions
        if ('depth' in sensor_params.streams and 'image' in sensor_params.streams):
            framesync[0] = niIsFrameSyncedWith(self.ni_device.depth_nodes[0], self.ni_device.image_nodes[0])


        # Init for each stream
        for stream in sensor_params.streams:
            # Time Stamp Dictionaries
            CurTimeStampList[stream]=0
            PrevTimeStampList[stream]=0
            DifTimeStampList[stream]=0
            # FrameID Dictionaries
            CurFrameIDList[stream]=0
            PrevFrameIDList[stream]=0
            self.bad_timestamp_frames[stream] = 0
            self.bad_timestamp_precent[stream] = 0
            self.bad_average_frames[stream] = 0
            self.bad_average_precent[stream] = 0

            # Stream Specific
            if stream == 'depth' :
                niGetMapOutputMode(self.ni_device.depth_nodes[0], cast(pointer(map_mode),c_void_p))
                StreamBufSize['depth'] = map_mode.nXRes * map_mode.nYRes
                StreamFPS['depth'] = map_mode.nFPS
                PyDepthBuffer = array.array("H",[0]*StreamBufSize['depth'])

            elif stream == 'image':
                niGetMapOutputMode(self.ni_device.image_nodes[0], cast(pointer(map_mode),c_void_p))
                StreamBufSize['image'] = map_mode.nXRes * map_mode.nYRes
                StreamFPS['image'] = map_mode.nFPS
                PyImageBuffer = array.array("B",[0]*(StreamBufSize['image']*sensor_params.bpp))

            elif stream =='IR':
                niGetMapOutputMode(self.ni_device.ir_nodes[0], cast(pointer(map_mode),c_void_p))
                StreamBufSize['IR'] = map_mode.nXRes * map_mode.nYRes
                StreamFPS['IR'] = map_mode.nFPS
                PyIRBuffer = array.array("B",[0]*(StreamBufSize['IR']*sensor_params.bpp))

            elif stream =='audio':
                rc = niGetWaveOutputMode(self.ni_device.audio_nodes[0], cast(pointer(wave_mode),c_void_p))
                required_data_size = [0]
                rc = niGetIntProperty(self.ni_device.audio_nodes[0],XN_STREAM_PROPERTY_REQUIRED_DATA_SIZE  , required_data_size)
                StreamBufSize['audio'] = required_data_size[0]
                PyAudioBuffer = array.array("B",[0]*StreamBufSize['audio'])


        # Read once
        if self.ni_device.depth_nodes != [] and niIsGenerating(self.ni_device.depth_nodes[0]):
            rc = niWaitOneUpdateAll(self.ni_device.ni_contexts[0] , self.ni_device.depth_nodes[0] )

        if self.ni_device.image_nodes != [] and niIsGenerating(self.ni_device.image_nodes[0]):
            rc = niWaitOneUpdateAll(self.ni_device.ni_contexts[0] , self.ni_device.image_nodes[0] )

        if self.ni_device.ir_nodes != [] and niIsGenerating(self.ni_device.ir_nodes[0]):
            rc = niWaitOneUpdateAll(self.ni_device.ni_contexts[0] , self.ni_device.ir_nodes[0] )

        if self.ni_device.audio_nodes != [] and niIsGenerating(self.ni_device.audio_nodes[0]):
            rc = niWaitOneUpdateAll(self.ni_device.ni_contexts[0] , self.ni_device.audio_nodes[0] )


        if rc != 0:
            err_string = niGetStatusString(rc)
            if framesync and err_string == "Didn't get any synched frame!":
                self.bad_framesync_frames += 1;
            else:
                self.test_result.string += "!Read: " + err_string + "\n"
                self.test_result.result = 1
                return

        # Set the timestamp for the PrevTimeStamp list

        for stream in sensor_params.streams:

            if stream == 'depth':
                TimeStamp[0] = niGetTimestamp(self.ni_device.depth_nodes[0])
                FrameID[0] = niGetFrameID(self.ni_device.depth_nodes[0])
            if stream == 'IR':
                TimeStamp[0] = niGetTimestamp(self.ni_device.ir_nodes[0])
                FrameID[0] = niGetFrameID(self.ni_device.ir_nodes[0])
            if stream == 'image':
                TimeStamp[0] = niGetTimestamp(self.ni_device.image_nodes[0])
                FrameID[0] = niGetFrameID(self.ni_device.image_nodes[0])
            if stream == 'audio':
                TimeStamp[0] = niGetTimestamp(self.ni_device.audio_nodes[0])
                FrameID[0] = niGetFrameID(self.ni_device.audio_nodes[0])




            PrevTimeStampList[stream] = TimeStamp[0]
            PrevFrameIDList[stream] = FrameID[0]

        if 'audio' in sensor_params.streams:
            buffer_size[0] = niGetDataSize(self.ni_device.audio_nodes[0])

        # Start taking frames
        for i in range(self.num_frames):


            if ___FramesInfoDebug___ == True:
                self.frames_info += "************** Test Frame No " + str(i) + " ********************\n"
            # Read from the device
            tic = time.clock()
            if self.ni_device.primary_stream_state == 'any':
                rc = niWaitAnyUpdateAll(self.ni_device.ni_contexts[0])

            elif self.ni_device.primary_stream_state == 'node':
                rc = niWaitOneUpdateAll(self.ni_device.ni_contexts[0] , self.ni_device.primary_stream_node)
            toc = time.clock()
            if ___FramesInfoDebug___ == True:
                self.frames_info += "Read Time - %.2f ms\n" % (1000*(toc-tic))


            if rc != 0 :
                err_string = niGetStatusString(rc)
                if framesync and (err_string == "Didn't get any synched frame!"):
                    self.bad_framesync_frames += 1;
                    continue
                else:
                    self.test_result.string += "!Read: " + err_string + "\n"
                    self.test_result.result = 1
                    return


            # ************Depth Actions *********************
            if 'depth' in sensor_params.streams:


                StreamBufAddr['depth'] = niGetDepthMap(self.ni_device.depth_nodes[0])
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "[-Depth Frame Info-]\n"
                # Test timeStamp
                TimeStamp[0] = niGetTimestamp(self.ni_device.depth_nodes[0])
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "Timestamp: %s\n" % (TimeStamp[0])


                CurTimeStampList['depth'] = TimeStamp[0]

                DifTimeStampList['depth'] = CurTimeStampList['depth']-PrevTimeStampList['depth']
                DifTimeStampList['depth'] = float(DifTimeStampList['depth']) / 1000.

                if __Debug__: print "Dif depth Time Stamp: ",DifTimeStampList['depth']
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* TimeStamp Diff : " + str(DifTimeStampList['depth']) + "\n"



                if (self.ni_device.primary_stream_state ==  'any') or ( NI_GetNodeTypeFromNodeHandle(self.ni_device.primary_stream_node) == NI_NODE_TYPE_DEPTH ):
                    if DifTimeStampList['depth']!=0:
                        if (DifTimeStampList['depth']) > self.config["TimeStampThresholdHigh" + str(StreamFPS['depth'])]:
                            self.bad_timestamp_frames['depth'] += 1
                            if __Debug__: print "Bad TimeStamp bigger"
                            if ___FramesInfoDebug___ == True:
                                self.frames_info += "! Bad Frame - Timestamp is too big\n"

                        elif (DifTimeStampList['depth']) < self.config["TimeStampThresholdLow" + str(StreamFPS['depth'])]:
                            self.bad_timestamp_frames['depth'] += 1
                            if __Debug__: print "Bad TimeStamp smaller"
                            if ___FramesInfoDebug___ == True:
                                self.frames_info += "! Bad Frame - Timestamp is too small\n"
                # Test Average
                PixelValue = 0
                AverageValue = 0


                NI_OSmemcpy(PyDepthBuffer.buffer_info()[0],StreamBufAddr['depth'],StreamBufSize['depth']*2)
                for pix in PyDepthBuffer:
                    if pix > 0 :
                        AverageValue = 1
                        break


                #AverageValue = AverageValue / StreamBufSize['depth']
                if __Debug__: print "Average depth pixel value is = " + str(AverageValue)
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* Average pixel value : " + str(AverageValue) + "\n"
                if AverageValue==0:
                    self.bad_average_frames['depth']+=1
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "! Bad Frame - Average is zero\n"
                # Test FrameID
                FrameID[0] = niGetFrameID(self.ni_device.depth_nodes[0])



                if __Debug__: print "Depth FrameID : ",FrameID[0]
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* FrameID value : " + str(FrameID[0]) + "\n"
                CurFrameIDList['depth'] = FrameID[0]
                if (CurFrameIDList['depth']-PrevFrameIDList['depth']) == 0:
                    new_depth = False
                else:
                    new_depth = True
                    if __Debug__: print "New Depth"
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "* Recognized new depth frame\n"
            else:
                new_depth = False


            # ************Image Actions *********************
            if 'image' in sensor_params.streams:
                StreamBufAddr['image'] = niGetImageMap(self.ni_device.image_nodes[0])
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "[-Image Frame Info-]\n"
                # Test timeStamp only if it's the primary stream or if any
                TimeStamp[0] = niGetTimestamp(self.ni_device.image_nodes[0])
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "Timestamp: %s\n" %  (TimeStamp[0])
                CurTimeStampList['image'] = TimeStamp[0]
                DifTimeStampList['image'] = CurTimeStampList['image']-PrevTimeStampList['image']
                DifTimeStampList['image'] = float(DifTimeStampList['image']) / 1000.
                if __Debug__: print "Dif image Time Stamp: ",DifTimeStampList['image']
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* TimeStamp Diff : " + str(DifTimeStampList['image']) + "\n"
                if (self.ni_device.primary_stream_state ==  'any') or ( NI_GetNodeTypeFromNodeHandle(self.ni_device.primary_stream_node) == NI_NODE_TYPE_IMAGE ):
                    if DifTimeStampList['image']!=0:
                        if (DifTimeStampList['image']) > self.config["TimeStampThresholdHigh" + str(StreamFPS['image'])]:
                            self.bad_timestamp_frames['image'] += 1
                            if __Debug__: print "Bad TimeStamp bigger"
                            if ___FramesInfoDebug___ == True:
                                self.frames_info += "! Bad Frame - Timestamp is too big\n"

                        elif (DifTimeStampList['image']) < self.config["TimeStampThresholdLow" + str(StreamFPS['image'])]:
                            self.bad_timestamp_frames['image'] += 1
                            if __Debug__: print "Bad TimeStamp smaller"
                            if ___FramesInfoDebug___ == True:
                                self.frames_info += "! Bad Frame - Timestamp is too small\n"
                # Test Average
                PixelValue = 0
                AverageValue = 0
                NI_OSmemcpy(PyImageBuffer.buffer_info()[0],StreamBufAddr['image'],StreamBufSize['image']*sensor_params.bpp)
                for pix in PyImageBuffer:
                    if pix > 0 :
                        AverageValue = 1
                        break
                #AverageValue = AverageValue / (StreamBufSize['image'] *3)
                if __Debug__: print "Average image pixel value is = " + str(AverageValue)
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* Average pixel value : " + str(AverageValue) + "\n"
                if AverageValue==0:
                    self.bad_average_frames['image']+=1
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "! Bad Frame - Average is zero\n"
                # Test FrameID
                FrameID[0] = niGetFrameID(self.ni_device.image_nodes[0])
                CurFrameIDList['image'] = FrameID[0]
                if __Debug__: print "Image FrameID : ",FrameID[0]
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* FrameID value : " + str(FrameID[0]) + "\n"
                if (CurFrameIDList['image']-PrevFrameIDList['image']) == 0:
                    new_image = False
                else:
                    new_image = True
                    if __Debug__: print "New Image"
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "* Recognized new image frame\n"
            else:
                new_image = False

            # ************IR Actions *********************
            if 'IR' in sensor_params.streams:

                StreamBufAddr['IR'] = niGetIRMap(self.ni_device.ir_nodes[0])
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "[-IR Frame Info-]\n"
                # Test timeStamp
                TimeStamp[0] = niGetTimestamp(self.ni_device.ir_nodes[0])
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "Timestamp: %s\n" % (TimeStamp[0])
                CurTimeStampList['IR'] = TimeStamp[0]
                DifTimeStampList['IR'] = CurTimeStampList['IR']-PrevTimeStampList['IR']
                DifTimeStampList['IR'] = float(DifTimeStampList['IR']) / 1000.
                if __Debug__: print "Dif IR Time Stamp: ",DifTimeStampList['IR']
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* TimeStamp Diff : " + str(DifTimeStampList['IR']) + "\n"
                if (self.ni_device.primary_stream_state ==  'any') or ( NI_GetNodeTypeFromNodeHandle(self.ni_device.primary_stream_node) == NI_NODE_TYPE_IR ):
                    if DifTimeStampList['IR']!=0:
                        if (DifTimeStampList['IR']) > self.config["TimeStampThresholdHigh" + str(StreamFPS['IR'])]:
                            self.bad_timestamp_frames['IR'] += 1
                            if __Debug__: print "Bad TimeStamp bigger"
                            if ___FramesInfoDebug___ == True:
                                self.frames_info += "! Bad Frame - Timestamp is too big\n"

                        elif (DifTimeStampList['IR']) < self.config["TimeStampThresholdLow" + str(StreamFPS['IR'])]:
                            self.bad_timestamp_frames['IR'] += 1
                            if __Debug__: print "Bad TimeStamp smaller"
                            if ___FramesInfoDebug___ == True:
                                self.frames_info += "! Bad Frame - Timestamp is too small\n"
                # Test Average
                PixelValue = 0
                AverageValue = 0
                NI_OSmemcpy(PyIRBuffer.buffer_info()[0],StreamBufAddr['IR'],StreamBufSize['IR']*sensor_params.bpp)
                for pix in PyIRBuffer:
                    if pix > 0 :
                        AverageValue = 1
                        break
                #AverageValue = AverageValue / (StreamBufSize['IR'] *3)
                if __Debug__: print "Average IR pixel value is = " + str(AverageValue)
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* Average pixel value : " + str(AverageValue) + "\n"
                if AverageValue==0:
                    self.bad_average_frames['IR']+=1
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "! Bad Frame - Average is zero\n"
                # Test FrameID
                FrameID[0] = niGetFrameID(self.ni_device.ir_nodes[0])
                if __Debug__: print "IR FrameID : ",FrameID[0]
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* FrameID value : " + str(FrameID[0]) + "\n"
                CurFrameIDList["IR"] = FrameID[0]
                if (CurFrameIDList['IR']-PrevFrameIDList['IR']) == 0:
                    new_IR = False
                else:
                    new_IR = True
                    if __Debug__: print "New IR"
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "* Recognized new IR frame\n"
            else:
                new_IR = False


            # ************Audio Actions *********************
            if 'audio' in sensor_params.streams:
                StreamBufAddr['audio'] = niGetAudioBuffer(self.ni_device.audio_nodes[0])
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "[-Audio Frame Info-]\n"

                # Test timeStamp
                TimeStamp[0] = niGetTimestamp(self.ni_device.audio_nodes[0])
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "Timestamp: %s\n" % (TimeStamp[0])
                CurTimeStampList['audio'] = TimeStamp[0]
                DifTimeStampList['audio'] = CurTimeStampList['audio']-PrevTimeStampList['audio']
                DifTimeStampList['audio'] = float(DifTimeStampList['audio']) / 1000.
                if __Debug__: print "Dif audio Time Stamp: ",DifTimeStampList['audio']
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* TimeStamp Diff : " + str(DifTimeStampList['audio']) + "\n"


                if (self.ni_device.primary_stream_state ==  'any') or ( NI_GetNodeTypeFromNodeHandle(self.ni_device.primary_stream_node) == NI_NODE_TYPE_AUDIO ):

                    if DifTimeStampList['audio']!=0:

                        ms_time = float(buffer_size[0] * 1000.)/ float(2. * wave_mode.nChannels * wave_mode.nSampleRate)

                        if ___FramesInfoDebug___ == True:
                            self.frames_info += " -*- Current timestamp:" + str(CurTimeStampList['audio']) + "\n"
                            self.frames_info += " -*- Previous timestamp: " + str(PrevTimeStampList['audio']) + "\n"
                            self.frames_info += " -*- Computed timestamp Diff: " + str(ms_time) + "\n"
                            self.frames_info += " -*- Data size: " + str(buffer_size[0]) + "\n"
                            self.frames_info += " -*- Number of channels: " + str(wave_mode.nChannels) + "\n"
                            self.frames_info += " -*- Samplerate: " + str(wave_mode.nSampleRate) + "\n"


                        buffer_size[0] = niGetDataSize(self.ni_device.audio_nodes[0])



                        if  abs(ms_time -  DifTimeStampList['audio']) > self.config["TimeStampThresholdAudio"]:
                            self.bad_timestamp_frames['audio'] += 1
                            if __Debug__: print "Bad Audio timestamp"
                            if ___FramesInfoDebug___ == True:
                                self.frames_info += "! Bad Audio timestamp\n"

                # Test Average
                #PixelValue = 0
                AverageValue = 0

                #raw_input()
                NI_OSmemcpy(PyAudioBuffer.buffer_info()[0],StreamBufAddr['audio'],StreamBufSize['audio'])
                for sample in PyAudioBuffer:
                    if sample > 0 :
                        AverageValue = 1
                        break

                if __Debug__: print "Average audio sample value is = " + str(AverageValue)
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* Average sample value : " + str(AverageValue) + "\n"
                if AverageValue==0:
                    self.bad_average_frames['audio']+=1
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "! Bad Sample - Average is zero\n"
                #Test new data

                is_new = [0]

                is_new[0] = niIsDataNew(self.ni_device.audio_nodes[0])


                if __Debug__: print "Audio new data : ",is_new[0]
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "* New data value : " + str(is_new[0]) + "\n"

                if (is_new[0] == 1):
                    new_audio = True
                    if __Debug__: print "New Audio data"
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "* Recognized new audio sample\n"
                else:
                    new_audio = False

            else:
                new_audio = False





            if self.ni_device.primary_stream_state ==  'any':
                if not(new_image) and not(new_depth) and not(new_IR) and not(new_audio):
                    self.bad_frameID_frames += 1
                    if __Debug__: print "Bad FrameID or Audio data any"
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "![-GENERAL--- Bad FrameID or Audio data : Any ----]\n"
            # Depth is the primary stream, need to check it
            elif NI_GetNodeTypeFromNodeHandle(self.ni_device.primary_stream_node) == NI_NODE_TYPE_DEPTH:
                if not(new_depth):
                    self.bad_frameID_frames += 1
                    if __Debug__: print "Bad FrameID Depth"
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "![-GENERAL--- Bad FrameID : Depth ----]\n"
            # Image is the primary stream
            elif NI_GetNodeTypeFromNodeHandle(self.ni_device.primary_stream_node) == NI_NODE_TYPE_IMAGE:
                if not(new_image):
                    self.bad_frameID_frames += 1
                    if __Debug__: print "Bad FrameID image"
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "![-GENERAL--- Bad FrameID : Image ----]\n"

            elif NI_GetNodeTypeFromNodeHandle(self.ni_device.primary_stream_node) == NI_NODE_TYPE_IR:
                if not(new_IR):
                    self.bad_frameID_frames += 1
                    if __Debug__: print "Bad FrameID image"
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "![-GENERAL--- Bad FrameID : Image ----]\n"

            elif NI_GetNodeTypeFromNodeHandle(self.ni_device.primary_stream_node) == NI_NODE_TYPE_AUDIO:
                if not(new_audio):
                    self.bad_frameID_frames += 1
                    if __Debug__: print "Bad audio new data"
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "![-GENERAL--- Bad new data : Audio ----]\n"




            # Test FrameSync only if depth and image are in the streams and framesync is on
            if (('depth' in sensor_params.streams) and ('image' in sensor_params.streams)) and framesync[0]==1:
                timestamp_diff = CurTimeStampList['depth']-CurTimeStampList['image']
                if __Debug__ : print "FrameSync Diff: " + str(timestamp_diff)
                if ___FramesInfoDebug___ == True:
                    self.frames_info += "[- FrameSync Testing-]\n"
                if abs(timestamp_diff) > 3000:
                    self.bad_framesync_frames += 1
                    if ___FramesInfoDebug___ == True:
                        self.frames_info += "! Bad Frame Sync Frame\n"

            # Copy Current lists to the Previous lists
            PrevTimeStampList = CurTimeStampList.copy()
            PrevFrameIDList = CurFrameIDList.copy()
            if __Debug__: print 'Tested frame ' ,i
            if __Debug__: print "*"*20

        # Calculating Precentage on the bad frames
        for stream in sensor_params.streams:
            self.bad_timestamp_precent[stream] = self.bad_timestamp_frames[stream]/float(self.num_frames)*100.0
            self.bad_average_precent[stream] = self.bad_average_frames[stream]/float(self.num_frames)*100.0

        self.bad_frameID_precent = self.bad_frameID_frames/(float(self.num_frames))*100.0
        self.bad_framesync_precent = self.bad_framesync_frames/(float(self.num_frames) * 2) * 100.0

        res_string = "~Finished With Results (Bad/NumOfFrames) - \n"
        for stream in sensor_params.streams:
            res_string += "~ " + stream.capitalize() + ": TimeStamp - " +str(self.bad_timestamp_frames[stream])+ "/" + str(self.num_frames)
            res_string += " Average - " +str(self.bad_average_frames[stream])+ "/" + str(self.num_frames) + "\n"



        res_string += "~ FrameID:" + str(self.bad_frameID_frames)
        res_string += " FrameSync:" + str(self.bad_framesync_frames)
        res_string += "\n"
        self.test_result.string += res_string


        # Testing for the FrameID precent
        if (self.bad_frameID_precent) > self.config["BadFrameIDPrecent"]:
            self.test_result.string += "!FrameID: Too many bad FrameID frames - "+ str(self.bad_frameID_precent) + "%\n"
            self.test_result.result = 1
        # Testing for the number of bad framesync precent
        if (self.bad_framesync_precent) > self.config["BadFrameSyncPrecent"]:
            self.test_result.string += "!FrameSync: Too many bad framesync frames - "+ str(self.bad_framesync_precent) + "%\n"
            self.test_result.result = 1
        for stream in sensor_params.streams:
            # Testing for the number of bad average precent
            if (self.bad_average_precent[stream]) > self.config["BadAverageFramesPrecent"]:
                self.test_result.string += "!Average-"+stream+": Too many bad average frames - "+ str(self.bad_average_precent[stream]) + "%\n"
                self.test_result.result = 1
            # Testing for the number of bad timestamp precent
            if (self.bad_timestamp_precent[stream]) > (self.config["BadTimeStampFramesPrecent_" + stream[0].upper() + stream[1:]]):
                self.test_result.string += "!TimeStamp-"+stream+": Too many bad timestamp frames - "+ str(self.bad_timestamp_precent[stream]) + "%\n"
                self.test_result.result = 1

if __name__ == "__main__":
    print "General Read Frame Correctness Test."

    test = NITest_GeneralReadFrameCorrectness(10)
    sp = SensorParams(streams = ['depth'],depth_res = 'vga')
    test.run(sp)
    print test.test_result
