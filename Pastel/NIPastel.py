#/****************************************************************************
#*   PASTEL                                                                  *
#*                                                                           *
#*   PrimeSense Software Testing Library - Version 2.0                       *
#*                                                                           *
#*                                                                           *
#*                                                                           *
#****************************************************************************/

#/****************************************************************************
#*                                                                           *
#*   Prime Sensor SDK 3.0                                                    *
#*   Copyright (C) 2006 Prime Sense Ltd. All Rights Reserved.                *
#*                                                                           *
#*   This file has been provided pursuant to a License Agreement containing  *
#*   restrictions on its use. This data contains valuable trade secrets      *
#*   and proprietary information of Prime Sense Inc. and is protected        *
#*                                                                           *
#****************************************************************************/
#!/usr/bin/env python

__version__ = "$Version: 2.0$"
__Debug__ = False

#----------------------------Imports-------------------------------------------#


import time
import os
import sys

from NIps import *
import NIGris


#--------------------- Tests Imports ------------------------------------------#

#from NITest_PowerReset import *
from NITest_Permutations import *
from NITest_ResetStability import *
#from NITest_DynamicStreams import *
#from NITest_Registration import *
#from NITest_HighResolutions import *
#from NITest_Cropping import *
#from NITest_Stability import *
#from NITest_FrameSync import *
#from NITest_StreamFeatures import *
#from NITest_PrimaryStream import *
#from NITest_ResetStability import *
#from NITest_SoftReset import *
#from NITest_VSync import *
#from NITest_Licensing import *
#from NITest_NodeDependency import *
#from NITest_MultiProcess import *
#from NITest_KillServer import *
#from NITest_Files import *
#from NITest_Callback import *
#from NITest_ServerShutdown import *
#from NITest_TimestampSync import *
#from NITest_MultiProcessRandom import *


#-----------------------------TestList Prototype-------------------------------#

class NITestList(NIBaseTest):
    def add_tests(self):
        pass

    def __init__(self, extra_tag=None, extra_value=None):
        NIBaseTest.__init__(self)
        self.test_list = []
        self.logs = {}

        sw_version, hw_version, openni_version, sensor_id = self.get_general_info()
        fh = open('NIPastel_General_Properties.txt', 'w')
        fh.write("Sensor Module Version = %s\n" % sw_version)
        fh.write("Hardware Version = %s\n" % hw_version)
        fh.write("OpenNI Version = %s\n" % openni_version)
        fh.write("Sensor ID = %s\n" % sensor_id)
        fh.close()

        tag_list = []
        value_list = []
        if sw_version != '':
            tag_list.append('Sensor Module Version')
            value_list.append(sw_version)
        if hw_version != '':
            tag_list.append('Hardware Version')
            value_list.append(hw_version)

        if openni_version != '':
            tag_list.append('OpenNI Version')
            value_list.append(openni_version)

        if sensor_id != '':
            tag_list.append('Sensor ID')
            value_list.append(sensor_id)

        if tag_list != [] and value_list != []:
            extra_tag = tag_list
            extra_value = value_list

        testlist_name = repr(self.__class__).partition(".")[-1][:-2]

        self.html_index = NIGris.HTMLIndex("./" + testlist_name + ".html", testlist_name, extra_tag, extra_value)
        self.add_tests()

    def get_general_info(self):

        sw_version = ''
        hw_version = ''
        openni_version = ''
        sensor_id = ''

        rc = self._open_sensor_general(SensorParams(streams=[]))

        if rc:
            version_struct = XnVersions()
            version_struct_p = pointer(version_struct)

            rc = niGetGeneralProperty(self.ni_device.device_nodes[0], XN_MODULE_PROPERTY_VERSION,
                                      sizeof(version_struct), version_struct_p)

            if rc == NI_STATUS_OK:
                #can get also the sensor module version (EE) from here
                #sw_version = '%s.%s.%s.%s' %(version_struct.SDK.nMajor,version_struct.SDK.nMinor,version_struct.SDK.nMaintenance,version_struct.SDK.nBuild)
                hw_version = '%s.%s.%s' % (version_struct.nMajor, version_struct.nMinor, version_struct.nBuild )

            sensor_id_p = create_string_buffer(100)
            rc = niGetStringProperty(self.ni_device.device_nodes[0], XN_MODULE_PROPERTY_ID, sensor_id_p)
            if rc == NI_STATUS_OK:
                sensor_id = sensor_id_p.value

            version_struct = NiVersion()
            version_struct_p = pointer(version_struct)
            niGetVersion(version_struct_p)
            openni_version = '%s.%s.%s.%s' % (
                version_struct.nMajor, version_struct.nMinor, version_struct.nMaintenance, version_struct.nBuild )

            node_info = niGetNodeInfo(self.ni_device.device_nodes[0])
            node_description = niNodeInfoGetDescription(node_info)
            description_ptr = cast(node_description, POINTER(NiProductionNodeDescription))
            sw_version = '%s.%s.%s.%s' % (description_ptr.contents.Version.nMajor, \
                                          description_ptr.contents.Version.nMinor, \
                                          description_ptr.contents.Version.nMaintenance, \
                                          description_ptr.contents.Version.nBuild)

        # if len(self.ni_device.ni_contexts) > 0:
        #     device = c_void_p()
        #     niFindExistingNodeByType(self.ni_device.ni_contexts[0], NI_NODE_TYPE_DEVICE, byref(device))
        #     if device:
        #         niSetIntProperty(device, "ServerNoClientsTimeout", 0)
        #         print "Killing Server - Versions getting function"

        self._close_sensor()
        time.sleep(1)
        return sw_version, hw_version, openni_version, sensor_id


    def run(self):
        try:


            bulk_tests_started = False
            for test in self.test_list:


                if sys.platform == 'win32':
                    os.system("taskkill /im EXCEL.exe /f 2>nul")
                    os.system("taskkill /im K8062e.exe /f 2>nul")

                # Get test name from module
                test_name = repr(test.__class__).partition(".")[-1][:-2]



                # if its permutations with capture mode, change name to capturemode
                if test_name == "NITest_Permutations":
                    if test.usb_mode == 0:
                        usb_string = "ISO"
                    elif test.usb_mode == 1:
                        usb_string = "BULK"

                #     test_name += '-' + usb_string
                # if test_name == "NITest_DynamicStreams":
                #     if test.usb_mode == 0:
                #         usb_string = ""
                #     elif test.usb_mode == 1:
                #         usb_string = "ISO"
                #     else:
                #         usb_string = "BULK"
                #         if (bulk_tests_started == False):
                #             # do something here when moving from ISO to BULK
                #             #os.system("taskkill /im XnSensorServer.exe /f 2>nul")
                #             #time.sleep(30)
                #             bulk_tests_started = True

                    test_name += '-' + usb_string

                print "\n"
                print "*" * 30 + test_name + "*" * 30 + "\n"
                print "\n"

                # Run the test

                tic = time.clock()

                test.run()

                toc = time.clock()

                test_time = 1000 * (toc - tic)

                if test.test_result.result == 0:
                    self.html_index.add(True, "./Results/" + test_name + ".html", test_name, test_time)
                    print "%%" + test_name + " Passed (%s).\n" % str(test_time)
                else:
                    self.html_index.add(False, "./Results/" + test_name + ".html", test_name, test_time)
                    self.test_result.result += 1
                    print "%%" + test_name + " Failed (%s).\n" % str(test_time)

                if sys.platform == 'win32':
                    os.system("taskkill /im EXCEL.exe /f 2>nul")
                    os.system("taskkill /im K8062e.exe /f 2>nul")

        except:
            if sys.platform == 'win32':
                os.system("taskkill /im EXCEL.exe /f 2>nul")
                os.system("taskkill /im K8062e.exe /f 2>nul")
            print "Exception!! , saving last log..."
            self.html_index.add(False, "./Results/" + test_name + ".html", test_name)
            raise


    def save_sdk_logs(self, dir_name):
        """ Save SDK Logs to a specific directory"""
        # create logs dir
        cwd = os.getcwd()
        try:
            os.mkdir(dir_name)
        except:
            pass
        os.chdir(dir_name)
        # save logs for every test
        for log_name in self.logs:
            logf = open(log_name + ".txt", 'w')
            logf.write(self.logs[log_name])
            logf.close()
        os.chdir(cwd)


#-----------------------------Test Lists---------------------------------------#


class NITestList_NightlyCapri(NITestList):
    def add_tests(self):
        self.test_list.append(NITest_Permutations(num_times = 40,num_frames=500, usb_mode=0))
        self.test_list.append(NITest_Permutations(num_times = 40,num_frames=500, usb_mode=1))
        self.test_list.append(NITest_ResetStability(read_frames = True,NumSoftResets=50,NumHardResets = 0))

class NITestList_Short(NITestList):
    def add_tests(self):
        self.test_list.append(NITest_Permutations(num_times = 1,num_frames=30, usb_mode=0))
        self.test_list.append(NITest_Permutations(num_times = 1,num_frames=30, usb_mode=1))
        self.test_list.append(NITest_ResetStability(read_frames = True,NumSoftResets=2,NumHardResets = 0))


#-------------------------------------Main-------------------------------------#


if __name__ == "__main__":
    Nightly = NITestList_Short()
    #Nightly.get_general_info()
    Nightly.run()
