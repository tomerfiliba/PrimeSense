from NIps import *
import glob
import NIGris
import time
import os
__Debug__ = True

print "PSYCO IS COMMENTED OUT!!!!!!!!!!!!!!!!!!!!"
#import psyco
#psyco.full()



#if sys.platform == 'win32':
#    server_log_dir = "c:\\Program Files\\Prime Sense\\Sensor\\Bin\\Log\\"
#else:
#    server_log_dir = "/var/log/primesense/XnSensorServer/"
server_log_dir = "./Log"

class TestResult(object):
    def __init__(self):
        self.string = ''
        self.result = 0
        self.log = ''
        self.html = ''

    def print_():
        print(self.String)
    def __str__(self):
        return self.string
    def __eval__(self):
        return self.string


class SensorParams(object):
    def __init__(self,**kwargs):

        self.streams = kwargs.get("streams",['depth','image'])
        self.depth_xres = kwargs.get("depth_xres",640)
        self.depth_yres =  kwargs.get("depth_yres",480)
        self.depth_fps = kwargs.get("depth_fps",30)
        self.depth_inputformat = kwargs.get("depth_inputformat",1)
        self.depth_outputformat = kwargs.get("depth_outputformat",1)
        self.image_xres = kwargs.get("image_xres",640)
        self.image_yres = kwargs.get("image_yres",480)
        self.image_fps = kwargs.get("image_fps",30)
        self.image_inputformat = kwargs.get("image_inputformat",1)
        self.image_outputformat = kwargs.get("image_outputformat",5)
        self.IR_xres = kwargs.get("IR_xres",640)
        self.IR_yres = kwargs.get("IR_yres",480)
        self.IR_fps = kwargs.get("IR_fps",30)
        self.ir_outputformat = kwargs.get("ir_outputformat",3)
        self.audio_samplerate = kwargs.get("audio_samplerate",48000)
        self.audio_channels = kwargs.get("audio_channels",2)
        if 'depth_res' in kwargs:
            if kwargs.get('depth_res')=='vga':
                self.depth_xres = kwargs.get("depth_xres",640)
                self.depth_yres =  kwargs.get("depth_yres",480)
            if kwargs.get('depth_res')=='qvga':
                self.depth_xres = kwargs.get("depth_xres",320)
                self.depth_yres =  kwargs.get("depth_yres",240)
        if 'image_res' in kwargs:
            if kwargs.get('image_res')=='vga':
                self.image_xres = kwargs.get("image_xres",640)
                self.image_yres =  kwargs.get("image_yres",480)
            if kwargs.get('image_res')=='qvga':
                self.image_xres = kwargs.get("image_xres",320)
                self.image_yres =  kwargs.get("image_yres",240)
            if kwargs.get('image_res')=='sxga':
                self.image_xres = kwargs.get("image_xres",1280)
                self.image_yres =  kwargs.get("image_yres",1024)
            if kwargs.get('image_res')=='uxga':
                self.image_xres = kwargs.get("image_xres",1600)
                self.image_yres =  kwargs.get("image_yres",1200)
        if 'IR_res' in kwargs:
            if kwargs.get('IR_res')=='vga':
                self.IR_xres = kwargs.get("IR_xres",640)
                self.IR_yres =  kwargs.get("IR_yres",480)
            if kwargs.get('IR_res')=='qvga':
                self.IR_xres = kwargs.get("IR_xres",320)
                self.IR_yres =  kwargs.get("IR_yres",240)
            if kwargs.get('IR_res')=='sxga':
                self.IR_xres = kwargs.get("IR_xres",1280)
                self.IR_yres =  kwargs.get("IR_yres",1024)

        # Bits per pixels
        # Output format. 2 - Gray8, 4 - YUV422, 5 - RGB24 (default)
        if ('image' in self.streams):
            if self.image_outputformat == 4:
                self.bpp = 2
            elif self.image_outputformat == 2:
                self.bpp = 1
            elif self.image_outputformat == 5:
                self.bpp = 3

        if ('IR' in self.streams):
            if self.ir_outputformat == 3:
                self.bpp = 2
            elif self.ir_outputformat == 5:
                self.bpp = 3

        # Valid / Invalid configuration
        if (self.depth_xres==640 and self.depth_yres==480 and self.depth_fps==60):
            self.valid = 0
        elif (self.IR_xres==640 and self.IR_yres==480 and self.IR_fps==60):
            self.valid = 0
        elif (self.image_xres==640 and self.image_yres==480 and self.image_fps==60):
            self.valid = 0
        # elif ('IR' in self.streams and 'depth' in self.streams) and (self.depth_xres != self.IR_xres):
        #     self.valid = 0
        # elif ('IR' in self.streams and 'depth' in self.streams) and (self.depth_yres != self.IR_yres):
        #     self.valid = 0
        # elif ('IR' in self.streams and 'depth' in self.streams) and (self.depth_fps != self.IR_fps):
        #     self.valid = 0
        # elif ('IR' in self.streams and 'image' in self.streams):
        #     self.valid = 0
        else:
            self.valid = 1

    def open_string(self):

        outs = ''
        for stream in self.streams:
            if stream == "depth":
                outs += "Depth[%s,%s,%s,%s,%s]" % (self.depth_xres,self.depth_yres,self.depth_fps,self.depth_inputformat,self.depth_outputformat)
            elif stream == "image":
                outs += "Image[%s,%s,%s,%s,%s]" % (self.image_xres,self.image_yres,self.image_fps,self.image_inputformat,self.image_outputformat)
            elif stream == "IR":
                outs += "IR[%s,%s,%s,%s]" % (self.IR_xres,self.IR_yres,self.IR_fps,self.ir_outputformat)
            elif stream == "audio":
                outs += "Audio[%s,%s]" % (self.audio_samplerate,self.audio_channels)
            if stream != self.streams[-1]:
                outs += ";"
        return outs

class NIBaseTest(object):
    def __init__(self):

        self.test_result = TestResult()
        self.html_log = NIGris.HTMLReport()
        self.ni_device = NiDevice()
        self._senosr_is_open = False


    def _open_file(self,filename):
        if self._senosr_is_open == False:
            # Start Log
            NI_LogInit()
            # Create device

            self.ni_device = NiDevice()
            self.ni_device.ni_contexts.append(c_void_p())
            rc = niInit(byref(self.ni_device.ni_contexts[0]))
            AddPrimeSenseLicense(self.ni_device.ni_contexts[0])

            rc = niContextOpenFileRecording(self.ni_device.ni_contexts[0],filename)
            if rc != 0:
                print "Error Opening File -",filename
                return rc

            pNodesList = c_void_p()
            rc = niEnumerateExistingNodesByType(self.ni_device.ni_contexts[0], NI_NODE_TYPE_PLAYER ,byref(pNodesList))
            pChosenIt = niNodeInfoListGetFirst(pNodesList)
            if (niNodeInfoListIteratorIsValid(pChosenIt)):
                pChosen = niNodeInfoListGetCurrent(pChosenIt)
                self.ni_device.player_nodes.append(niNodeInfoGetHandle(pChosen))
            niNodeInfoListFree (pNodesList)


            pNodesList = c_void_p()
            rc = niEnumerateExistingNodesByType(self.ni_device.ni_contexts[0], NI_NODE_TYPE_DEPTH ,byref(pNodesList))
            pChosenIt = niNodeInfoListGetFirst(pNodesList)
            if (niNodeInfoListIteratorIsValid(pChosenIt)):
                pChosen = niNodeInfoListGetCurrent(pChosenIt)
                self.ni_device.depth_nodes.append(niNodeInfoGetHandle(pChosen))
            niNodeInfoListFree (pNodesList)

            pNodesList = c_void_p()
            rc = niEnumerateExistingNodesByType(self.ni_device.ni_contexts[0], NI_NODE_TYPE_IMAGE ,byref(pNodesList))
            pChosenIt = niNodeInfoListGetFirst(pNodesList)
            if (niNodeInfoListIteratorIsValid(pChosenIt)):
                pChosen = niNodeInfoListGetCurrent(pChosenIt)
                self.ni_device.image_nodes.append(niNodeInfoGetHandle(pChosen))
            niNodeInfoListFree (pNodesList)

            pNodesList = c_void_p()
            rc = niEnumerateExistingNodesByType(self.ni_device.ni_contexts[0], NI_NODE_TYPE_IR ,byref(pNodesList))
            pChosenIt = niNodeInfoListGetFirst(pNodesList)
            if (niNodeInfoListIteratorIsValid(pChosenIt)):
                pChosen = niNodeInfoListGetCurrent(pChosenIt)
                self.ni_device.ir_nodes.append(niNodeInfoGetHandle(pChosen))
            niNodeInfoListFree (pNodesList)


            pNodesList = c_void_p()
            rc = niEnumerateExistingNodesByType(self.ni_device.ni_contexts[0], NI_NODE_TYPE_AUDIO ,byref(pNodesList))
            pChosenIt = niNodeInfoListGetFirst(pNodesList)
            if (niNodeInfoListIteratorIsValid(pChosenIt)):
                pChosen = niNodeInfoListGetCurrent(pChosenIt)
                self.ni_device.audio_nodes.append(niNodeInfoGetHandle(pChosen))
            niNodeInfoListFree (pNodesList)

            if (rc != NI_STATUS_OK):
                err_string = niGetStatusString(rc)
                self.test_result.string += "!OpenFile: "+ err_string + "\n"
                self.test_result.result = 1
                self._senosr_is_open = True
                sdk = self._close_sensor()
                self.html_log.add(False,self.test_result.string,sdk)
                return False

            self._senosr_is_open = True
            return True




    def _open_sensor(self,sp,usb_mode = 0,log_sdk_on_fail_only = True, extra_string = ''):

        self.ni_device = NiDevice()
        if self._senosr_is_open == False:
            # Check for 16 bit uncompressed depth in VGA
            if ('depth' in sp.streams and sp.depth_inputformat == 0):
                if __Debug__: print "16 bit Uncompressed depth, not testing."
                self.html_log.add(True,extra_string + "16 bit Uncompressed depth, not testing.",'')
                return False

            #if ('audio' in sp.streams) and (usb_mode == 1):
            #    if __Debug__: print "Audio in ISO configuration, not testing."
            #    self.html_log.add(True,"Audio in ISO configuration, not testing.",'')
            #    return False

            if ('depth' in sp.streams) and (usb_mode == 2) and (sp.depth_inputformat== 3):
                if __Debug__: print "11 bit Uncompressed depth in BULK, not testing."
                self.html_log.add(True,extra_string + "11 bit Uncompressed depth in BULK, not testing.",'')
                return False

            if ('image' in sp.streams) and (usb_mode == 2) and (sp.image_inputformat== 5):
                if __Debug__: print "Uncompressed YUV Image in BULK configuration, not testing."
                self.html_log.add(True,extra_string + "Uncompressed YUV Image in BULK configuration, not testing.",'')
                return False


            # Start Log

            NI_LogInit()



            # Open Device
            rc = OpenNIContext(self.ni_device, sp.open_string(),usb_mode)


            if ((rc != NI_STATUS_OK) and sp.valid):
                err_string = niGetStatusString(rc)
                self.test_result.result += 1
                self._senosr_is_open = True
                sdk_log = self._close_sensor()
                self.html_log.add(False,extra_string + "!OpenDevice: " + sp.open_string() + " : "+ err_string + "\n",sdk_log)
                return False
            elif (rc != NI_STATUS_OK) and not(sp.valid):
                #self.test_result.result = 0
                self._senosr_is_open = True
                sdk_log = self._close_sensor()
                if (log_sdk_on_fail_only == True):
                    sdk_log = ''
                self.html_log.add(True,extra_string + sp.open_string() + " - Failure Assertion Passed\n",sdk_log)
                return False

            self._senosr_is_open = True
            return True


    def _open_sensor_general(self,sp,usb_mode = 0,log_sdk_on_fail_only = True):

        self.ni_device = NiDevice()
        if self._senosr_is_open == False:
            NI_LogInit()

            # Open Device
            rc = OpenNIContext(self.ni_device, sp.open_string(),usb_mode)

            if ((rc != NI_STATUS_OK) and sp.valid):
                self._senosr_is_open = True
                self._close_sensor()
                return False

            self._senosr_is_open = True
            return True





    def _configure_sensor(self,sp,usb_mode = 0,log_sdk_on_fail_only = True, extra_string = ''):


        # Check for 16 bit uncompressed depth in VGA
        if ('depth' in sp.streams and sp.depth_inputformat == 0):
            if __Debug__: print "16 bit Uncompressed depth, not testing."
            self.html_log.add(True,extra_string + "16 bit Uncompressed depth, not testing.",'')
            return False

        #if ('audio' in sp.streams) and (usb_mode == 1):
        #    if __Debug__: print "Audio in ISO configuration, not testing."
        #    self.html_log.add(True,"Audio in ISO configuration, not testing.",'')
        #    return False

        if ('depth' in sp.streams) and (usb_mode == 2) and (sp.depth_inputformat== 3):
            if __Debug__: print "11 bit Uncompressed depth in BULK, not testing."
            self.html_log.add(True,extra_string + "11 bit Uncompressed depth in BULK, not testing.",'')
            return False


        if ('image' in sp.streams) and (usb_mode == 2) and (sp.image_inputformat== 5):
            if __Debug__: print "Uncompressed YUV Image in BULK configuration, not testing."
            self.html_log.add(True,extra_string + "Uncompressed YUV Image in BULK configuration, not testing.",'')
            return False

        # Start Log
        #PS_LogInit()

        # Configure Device

        rc,conf_err_str = ConfigureNIContext(self.ni_device, sp.open_string())



        if ((rc != NI_STATUS_OK) and sp.valid):
            err_string = niGetStatusString(rc)
            self.test_result.result += 1
            sdk_log = get_last_log()
            self.html_log.add(False, extra_string + conf_err_str + "\n!ConfigureDevice: " + sp.open_string() + " : "+ err_string + "\n",sdk_log)
            return False
        elif (rc != NI_STATUS_OK) and not(sp.valid):
            #self.test_result.result = 0
            sdk_log = get_last_log()
            if (log_sdk_on_fail_only == True):
                sdk_log = ''
            self.html_log.add(True,extra_string + sp.open_string() + " - Failure Assertion Passed\n",sdk_log)
            return False

        return True



    def _read_rc(self):

        if self._senosr_is_open == True:
            if self.ni_device.primary_stream_state == 'any':
                rc = niWaitAnyUpdateAll(self.ni_device.ni_contexts[0])
            elif self.ni_device.primary_stream_state == 'node':
                rc = niWaitOneUpdateAll(self.ni_device.ni_contexts[0] , self.ni_device.primary_stream_node)


            return rc

    def _read(self):

        if self._senosr_is_open == True:
            if self.ni_device.primary_stream_state == 'any':
                rc = niWaitAnyUpdateAll(self.ni_device.ni_contexts[0])
            elif self.ni_device.primary_stream_state == 'node':
                rc = niWaitOneUpdateAll(self.ni_device.ni_contexts[0] , self.ni_device.primary_stream_node)

            if rc != NI_STATUS_OK:


                err_string = niGetStatusString(rc)

                print 'Read error', err_string
                self.test_result.result = 1



                sdk_log = self._close_sensor()
                self.html_log.add(False,"!Read: "+ err_string + "\n",sdk_log)
                return False
            return True


    def _close_sensor(self):

        if self._senosr_is_open == True:
            device = c_void_p()
            NI_LogClose()
            self._close_server_log()
            if len(self.ni_device.device_nodes) > 0:
                niSetIntProperty(self.ni_device.device_nodes[0], "FWLog" ,0)

            niShutdown(self.ni_device.ni_contexts[0])


            self.ni_device = NiDevice()

            self._senosr_is_open = False
            return get_last_log()


    def _close_server_log(self):
        # close the server log
        device = c_void_p()
        niFindExistingNodeByType(self.ni_device.ni_contexts[0],NI_NODE_TYPE_DEVICE, byref(device))
        if device:
            niSetIntProperty(device,"ServerStartNewLogFile", 1)



def glob_by_date(str):
    date_file_list = []
    for file in glob.glob(str):
        stats = os.stat(file)
        lastmod_date = time.localtime(stats[8])
        date_file_tuple = lastmod_date, file
        date_file_list.append(date_file_tuple)
    date_file_list.sort()
    return date_file_list

def get_last_log():
    # try:
        cwd = os.getcwd()
        os.chdir("./Log")
        #open last file in log dir

        fw_log_string = "FW log not found"
        last_log_file = glob_by_date("*.FirmwareLog.log")
        if last_log_file != []:
            log_file = open(last_log_file[-1][1],"r")
            fw_log_string = log_file.read()
            log_file.close()
            os.remove(last_log_file[-1][1])

        log_string = "SDK log not found"
        last_log_file = glob_by_date("*.log")
        if last_log_file != []:
            log_file = open(last_log_file[-1][1],"r")
            log_string = log_file.read()
            log_file.close()
            os.remove(last_log_file[-1][1])

        os.chdir(cwd)
        return log_string + "\n\n" + fw_log_string
    # except :
    #     os.chdir(cwd)
    #     return "Exception in log passing function.\n"



def AddNodeToContext(ni_device, node_type):

    pNodesList = c_void_p()
    rc = niEnumerateProductionTrees(ni_device.ni_contexts[0], node_type, 0, byref(pNodesList))
    if (rc != 0):
        return rc

    pChosenIt = niNodeInfoListGetFirst(pNodesList)
    pChosen = niNodeInfoListGetCurrent(pChosenIt)

    if (node_type == NI_NODE_TYPE_DEVICE):
        ni_device.device_nodes.append(c_void_p())
        rc = niCreateProductionTree(ni_device.ni_contexts[0], pChosen, byref(ni_device.device_nodes[0]))
    elif (node_type == NI_NODE_TYPE_DEPTH):
        ni_device.depth_nodes.append(c_void_p())
        rc = niCreateProductionTree(ni_device.ni_contexts[0], pChosen, byref(ni_device.depth_nodes[0]))

    elif (node_type == NI_NODE_TYPE_AUDIO):
        ni_device.audio_nodes.append(c_void_p())
        rc = niCreateProductionTree(ni_device.ni_contexts[0], pChosen, byref(ni_device.audio_nodes[0]))
    elif (node_type == NI_NODE_TYPE_IR):
        ni_device.ir_nodes.append(c_void_p())
        rc = niCreateProductionTree(ni_device.ni_contexts[0], pChosen, byref(ni_device.ir_nodes[0]))
    elif (node_type == NI_NODE_TYPE_IMAGE):
        ni_device.image_nodes.append(c_void_p())
        rc = niCreateProductionTree(ni_device.ni_contexts[0], pChosen, byref(ni_device.image_nodes[0]))

    if (rc != 0):
        return rc

    niNodeInfoListFree (pNodesList)

    return rc



def OpenNIContext(ni_device, StrStreamFormat,USB_Mode = 0):

    # Parse the Stream format x="Image[333,444,55];Depth[3,24,4]" into x1="Image[333,444,55]", x2="Depth[3,24,4]"
    StreamArray = StrStreamFormat.split(';')
    ArraySize = len(StreamArray)
    wave_mode = NiWaveOutputMode()
    map_mode = NiMapOutputMode()
    ni_device.ni_contexts.append(c_void_p())
    rc = niInit(byref(ni_device.ni_contexts[0]))

    if (rc != 0):
        print 'niInit'
        return rc

    rc = AddNodeToContext(ni_device, NI_NODE_TYPE_DEVICE)
    if (rc != 0):
        print 'add node device'
        return rc


    rc = 0
    rc = niSetIntProperty(ni_device.device_nodes[0], "UsbInterface" ,USB_Mode )
    print 'USB result:', rc
    if (rc != 0):
        return rc

    # Enable the FW log
    rc = niSetIntProperty(ni_device.device_nodes[0], "FWLog" ,1)



    
    for item in StreamArray:
    
    
        OneItem = item.strip()
    
        if OneItem.lower().find('depth') > -1 or OneItem.lower().find('image') > -1 or OneItem.lower().find('ir') > -1:
            VectorCoords = OneItem[OneItem.find('[')+1:OneItem.find(']')]
            VectorCoordList = VectorCoords.split(',')
            map_mode.nXRes = int(VectorCoordList[0].strip())
            map_mode.nYRes = int(VectorCoordList[1].strip())
            map_mode.nFPS  = int(VectorCoordList[2].strip())
    
        if OneItem.lower().find('depth') > -1:
    
            rc = AddNodeToContext(ni_device, NI_NODE_TYPE_DEPTH)
            if (rc != 0):
                print 'add node depth'
                return rc
            rc = niSetMapOutputMode(ni_device.depth_nodes[0], cast(pointer(map_mode),c_void_p))
            if (rc != 0):
                print 'set depth output node'
                return rc
    
    
            # incase Pastel default is different than NI defaule
            #rc = niSetIntProperty(ni_device.depth_nodes[0], XN_STREAM_PROPERTY_INPUT_FORMAT ,1 )
            #if (rc != 0):
            #    print 'depth input format default'
            #    return rc
            #rc = niSetIntProperty(ni_device.depth_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,1 )
            #
            #if (rc != 0):
            #    print 'depth output format default'
            #    return rc
            ## incase Pastel default is different than NI defaule
            #
            #if len(VectorCoordList)>3:
            #    InpFor = int(VectorCoordList[3].strip())
            #    rc = niSetIntProperty(ni_device.depth_nodes[0], XN_STREAM_PROPERTY_INPUT_FORMAT ,InpFor )
            #    if (rc != 0):
            #        print 'depth input format'
            #        return rc
            #
            #if len(VectorCoordList)==5:
            #    OutFor = int(VectorCoordList[4].strip())
            #    rc = niSetIntProperty(ni_device.depth_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,OutFor )
            #    if (rc != 0):
            #        print 'depth output format'
            #        return rc
    
    
    
    
        elif OneItem.lower().find('image') > -1:
            rc = AddNodeToContext(ni_device, NI_NODE_TYPE_IMAGE)
            if (rc != 0):
                print 'add node image'
                return rc
            rc = niSetMapOutputMode(ni_device.image_nodes[0], cast(pointer(map_mode),c_void_p))
            if (rc != 0):
                print 'set image output node'
                return rc
    
            # incase Pastel default is different than NI defaule
            rc = niSetIntProperty(ni_device.image_nodes[0], XN_STREAM_PROPERTY_INPUT_FORMAT ,1 )
            if (rc != 0):
                print 'image input format default'
                return rc
            rc = niSetIntProperty(ni_device.image_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,5 )
            if (rc != 0):
                print 'image output format default'
                return rc
            # incase Pastel default is different than NI defaule
    
    
            if len(VectorCoordList)>3:
                InpFor = int(VectorCoordList[3].strip())
                rc = niSetIntProperty(ni_device.image_nodes[0], XN_STREAM_PROPERTY_INPUT_FORMAT ,InpFor )
                if (rc != 0):
                    print 'image input format'
                    return rc
    
            if len(VectorCoordList)==5:
                OutFor = int(VectorCoordList[4].strip())
                rc = niSetIntProperty(ni_device.image_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,OutFor )
                if (rc != 0):
                    print 'image output format'
                    return rc
    
    
    
        elif OneItem.lower().find('ir') > -1:
    
            rc = AddNodeToContext(ni_device, NI_NODE_TYPE_IR)
            if (rc != 0):
                print 'add node IR'
                return rc
    
    
            rc = niSetMapOutputMode(ni_device.ir_nodes[0], cast(pointer(map_mode),c_void_p))
            if (rc != 0):
                print 'set image output node'
                return rc

            # TODO: Fix the input / output mode issues
            # incase Pastel default is different than NI defaule
            #rc = niSetIntProperty(ni_device.ir_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,5 )
            #if (rc != 0):
            #    print 'IR output format default'
            #    return rc
            # incase Pastel default is different than NI defaule
    
            #if len(VectorCoordList)==4:
            #    OutFor = int(VectorCoordList[3].strip())
            #    rc = niSetIntProperty(ni_device.ir_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,OutFor )
            #    if (rc != 0):
            #        print 'IR output format'
            #        return rc
    
    
    
        elif OneItem.lower().find('audio') > -1:
    
            rc = AddNodeToContext(ni_device, NI_NODE_TYPE_AUDIO)
            if (rc != 0):
                print 'add node audio'
                return rc
    
            VectorCoords = OneItem[OneItem.find('[')+1:OneItem.find(']')]
            VectorCoordList = VectorCoords.split(',')
    
            wave_mode.nSampleRate = int(VectorCoordList[0].strip())
            wave_mode.nChannels = int(VectorCoordList[1].strip())
            wave_mode.nBitsPerSample = 16
    
            rc = niSetWaveOutputMode( ni_device.audio_nodes[0], cast(pointer(wave_mode),c_void_p))
            if (rc != 0):
                print 'set audio output node'
                return rc


    # Add the device


    rc = niStartGeneratingAll(ni_device.ni_contexts[0])

    if (rc != 0):
        print 'start generating all'
        print rc,  niGetStatusString(rc)
        return rc

    return rc



def InitNiContext(ni_device,streams,usb_mode=1):

    ni_device.ni_contexts.append(c_void_p())
    rc = niInit(byref(ni_device.ni_contexts[0]))
    AddPrimeSenseLicense(ni_device.ni_contexts[0])

    if (rc != 0):
        return rc

    rc = AddNodeToContext(ni_device, NI_NODE_TYPE_DEVICE)
    if (rc != 0):
        return rc


    #rc = niSetIntProperty(ni_device.device_nodes[0], XN_MODULE_PROPERTY_USB_INTERFACE ,usb_mode )
    #print 'USB result:', rc
    #if (rc != 0):
    #    return rc


    for stream in streams:
        if (stream.lower() == 'depth' ):
            rc = AddNodeToContext(ni_device, NI_NODE_TYPE_DEPTH)
            if (rc != 0):
                return rc
        elif (stream.lower() == 'image' ):
            rc = AddNodeToContext(ni_device, NI_NODE_TYPE_IMAGE)
            if (rc != 0):
                return rc
        elif (stream.lower() == 'ir' ):
            rc = AddNodeToContext(ni_device, NI_NODE_TYPE_IR)
            if (rc != 0):
                return rc
        elif (stream.lower() == 'audio' ):
            rc = AddNodeToContext(ni_device, NI_NODE_TYPE_AUDIO)
            if (rc != 0):
                return rc

    return rc

def ConfigureNIContext(ni_device, StrStreamFormat):


    # Parse the Stream format x="Image[333,444,55];Depth[3,24,4]" into x1="Image[333,444,55]", x2="Depth[3,24,4]"
    StreamArray = StrStreamFormat.split(';')
    ArraySize = len(StreamArray)

    wave_mode = NiWaveOutputMode()
    map_mode = NiMapOutputMode()

    streams_to_open = []

    rc = niStopGeneratingAll(ni_device.ni_contexts[0])
    if (rc != 0):
        print 'niStopGeneratingAll', rc, niGetStatusString(rc)
        return rc, 'niStopGeneratingAll NI context'


    for item in StreamArray:

        OneItem = item.strip()





        if OneItem.lower().find('depth') > -1 or OneItem.lower().find('image') > -1 or OneItem.lower().find('ir') > -1:
            VectorCoords = OneItem[OneItem.find('[')+1:OneItem.find(']')]
            VectorCoordList = VectorCoords.split(',')
            map_mode.nXRes = int(VectorCoordList[0].strip())
            map_mode.nYRes = int(VectorCoordList[1].strip())
            map_mode.nFPS  = int(VectorCoordList[2].strip())


        # If Stream is depth
        #if OneItem.lower().find('depth') > -1:
        #
        #    streams_to_open.append('depth')
        #
        #    rc = niSetMapOutputMode(ni_device.depth_nodes[0], cast(pointer(map_mode),c_void_p))
        #    if (rc != 0):
        #        return rc, 'niSetMapOutputMode depth '+ str(map_mode.nXRes) + ' ' + str(map_mode.nYRes) + ' ' + str(map_mode.nFPS)
        #    
        #    # incase Pastel default is different than NI defaule
        #    rc = niSetIntProperty(ni_device.depth_nodes[0], XN_STREAM_PROPERTY_INPUT_FORMAT ,1 )
        #    if (rc != 0):
        #        return rc, 'PASTEL default niSetIntProperty depth XN_STREAM_PROPERTY_INPUT_FORMAT 1'
        #    rc = niSetIntProperty(ni_device.depth_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,1 )
        #    if (rc != 0):
        #        return rc, 'PASTEL default niSetIntProperty depth XN_STREAM_PROPERTY_OUTPUT_FORMAT 1'
        #    # incase Pastel default is different than NI defaule
        #    
        #    if len(VectorCoordList)>3:
        #        InpFor = int(VectorCoordList[3].strip())
        #        rc = niSetIntProperty(ni_device.depth_nodes[0], XN_STREAM_PROPERTY_INPUT_FORMAT ,InpFor )
        #        if (rc != 0):
        #            return rc, 'niSetIntProperty depth XN_STREAM_PROPERTY_INPUT_FORMAT ' + str(InpFor)
        #    
        #    if len(VectorCoordList)==5:
        #        OutFor = int(VectorCoordList[4].strip())
        #        rc = niSetIntProperty(ni_device.depth_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,OutFor )
        #        if (rc != 0):
        #            return rc, 'niSetIntProperty depth XN_STREAM_PROPERTY_OUTPUT_FORMAT ' + str(OutFor)
        #
        #elif OneItem.lower().find('image') > -1:
        #
        #    streams_to_open.append('image')
        #
        #    rc = niSetMapOutputMode(ni_device.image_nodes[0], cast(pointer(map_mode),c_void_p))
        #    if (rc != 0):
        #        return rc, 'niSetMapOutputMode image '+ str(map_mode.nXRes) + ' ' + str(map_mode.nYRes) + ' ' + str(map_mode.nFPS)
        #
        #    # incase Pastel default is different than NI defaule
        #    rc = niSetIntProperty(ni_device.image_nodes[0], XN_STREAM_PROPERTY_INPUT_FORMAT ,1 )
        #    if (rc != 0):
        #        return rc, 'PASTEL default niSetIntProperty image XN_STREAM_PROPERTY_INPUT_FORMAT 1'
        #    rc = niSetIntProperty(ni_device.image_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,5 )
        #    if (rc != 0):
        #        return rc, 'PASTEL default niSetIntProperty image XN_STREAM_PROPERTY_OUTPUT_FORMAT 5'
        #    # incase Pastel default is different than NI defaule
        #
        #
        #    if len(VectorCoordList)>3:
        #        InpFor = int(VectorCoordList[3].strip())
        #        rc = niSetIntProperty(ni_device.image_nodes[0], XN_STREAM_PROPERTY_INPUT_FORMAT ,InpFor )
        #        if (rc != 0):
        #            return rc, 'niSetIntProperty image XN_STREAM_PROPERTY_INPUT_FORMAT ' + str(InpFor)
        #
        #    if len(VectorCoordList)==5:
        #        OutFor = int(VectorCoordList[4].strip())
        #        rc = niSetIntProperty(ni_device.image_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,OutFor )
        #        if (rc != 0):
        #            return rc, 'niSetIntProperty image XN_STREAM_PROPERTY_OUTPUT_FORMAT ' + str(OutFor)
        #
        ##elif OneItem.lower().find('ir') > -1:
        #
        #    streams_to_open.append('ir')
        #
        #    rc = niSetMapOutputMode(ni_device.ir_nodes[0], cast(pointer(map_mode),c_void_p))
        #    if (rc != 0):
        #        return rc, 'niSetMapOutputMode IR '+ str(map_mode.nXRes) + ' ' + str(map_mode.nYRes) + ' ' + str(map_mode.nFPS)
        #
        #    # incase Pastel default is different than NI defaule
        #    rc = niSetIntProperty(ni_device.ir_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,5 )
        #    if (rc != 0):
        #        return rc,'PASTEL default niSetIntProperty IR XN_STREAM_PROPERTY_OUTPUT_FORMAT 5'
        #    # incase Pastel default is different than NI defaule
        #
        #    if len(VectorCoordList)==4:
        #        OutFor = int(VectorCoordList[3].strip())
        #        rc = niSetIntProperty(ni_device.ir_nodes[0], XN_STREAM_PROPERTY_OUTPUT_FORMAT ,OutFor )
        #        if (rc != 0):
        #            return rc, 'niSetIntProperty IR XN_STREAM_PROPERTY_OUTPUT_FORMAT ' + str(OutFor)
        #
        #elif OneItem.lower().find('audio') > -1:
        #
        #    streams_to_open.append('audio')
        #
        #    VectorCoords = OneItem[OneItem.find('[')+1:OneItem.find(']')]
        #    VectorCoordList = VectorCoords.split(',')
        #
        #    wave_mode.nSampleRate = int(VectorCoordList[0].strip())
        #    wave_mode.nChannels = int(VectorCoordList[1].strip())
        #    wave_mode.nBitsPerSample = 16
        #
        #    rc = niSetWaveOutputMode( ni_device.audio_nodes[0], cast(pointer(wave_mode),c_void_p))
        #    if (rc != 0):
        #        return rc, 'niSetWaveOutputMode audio '+ str(wave_mode.nSampleRate) + ' ' + str(wave_mode.nChannels) + ' ' + str(wave_mode.nBitsPerSample)

    streams_to_open =  random.sample(streams_to_open,len(streams_to_open))

    for stream_str in streams_to_open:
        if (stream_str.lower() == 'depth' ):
            rc = niStartGenerating(ni_device.depth_nodes[0])
        if (stream_str.lower() == 'image'):
            rc = niStartGenerating(ni_device.image_nodes[0])
        if (stream_str.lower() == 'ir'):
            rc = niStartGenerating(ni_device.ir_nodes[0])
        if (stream_str.lower() == 'audio'):
            rc = niStartGenerating(ni_device.audio_nodes[0])

        if (rc != 0):
            return rc, 'niStartGenerating ' + stream_str





    return rc, ''
