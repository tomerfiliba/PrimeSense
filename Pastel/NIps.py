OUTPUT_LOG = False
OUTPUT_LOG_MODE = 'ALL'


# 'ALL'
# 'RETURN_VALUES'
# 'RETURN_VALUES_NOT_ZERO'


import sys, traceback
import string
import array
import os
import random
import datetime
from ctypes import *


if sys.platform == 'win32':
    cli=cdll.openNI
else:
    cli=cdll.LoadLibrary("libOpenNI.so")
    libc=CDLL("/lib/libc.so.6")


def WriteLog(log_line):
    if OUTPUT_LOG and OUTPUT_LOG_MODE == 'ALL':
        print 'OpenNI python wrapper %s: %s' % (datetime.datetime.now(),log_line)
    elif OUTPUT_LOG and OUTPUT_LOG_MODE == 'RETURN_VALUES':
        if 'return value' in log_line:
            print 'OpenNI python wrapper %s: %s' % (datetime.datetime.now(),log_line)
    elif OUTPUT_LOG and OUTPUT_LOG_MODE == 'RETURN_VALUES_NOT_ZERO':
        if 'return value' in log_line and 'return value: 0' not in log_line:
            print 'OpenNI python wrapper %s: %s' % (datetime.datetime.now(),log_line)


#################################
#### Enums, Structs, defines ####
#################################


# NiLogSeverity enum
(NI_LOG_VERBOSE, \
 NI_LOG_INFO, \
 NI_LOG_WARNING, \
 NI_LOG_ERROR) \
 = range(4)

# NiProductionNodeType enum
(NI_NODE_TYPE_DEVICE, \
 NI_NODE_TYPE_DEPTH, \
 NI_NODE_TYPE_IMAGE, \
 NI_NODE_TYPE_AUDIO, \
 NI_NODE_TYPE_IR, \
 NI_NODE_TYPE_USER, \
 NI_NODE_TYPE_RECORDER, \
 NI_NODE_TYPE_PLAYER, \
 NI_NODE_TYPE_GESTURE, \
 NI_NODE_TYPE_SCENE, \
 NI_NODE_TYPE_HANDS) \
 = range(1,12)


NODE_TYPE_TO_STRING = \
['NONE', \
 'NI_NODE_TYPE_DEVICE', \
 'NI_NODE_TYPE_DEPTH', \
 'NI_NODE_TYPE_IMAGE', \
 'NI_NODE_TYPE_AUDIO', \
 'NI_NODE_TYPE_IR', \
 'NI_NODE_TYPE_USER', \
 'NI_NODE_TYPE_RECORDER', \
 'NI_NODE_TYPE_PLAYER', \
 'NI_NODE_TYPE_GESTURE', \
 'NI_NODE_TYPE_SCENE', \
 'NI_NODE_TYPE_HANDS']


# NiPixelFormat enum
(NI_PIXEL_FORMAT_RGB24, \
 NI_PIXEL_FORMAT_YUV422, \
 NI_PIXEL_FORMAT_GRAYSCALE_8_BIT, \
 NI_PIXEL_FORMAT_GRAYSCALE_16_BIT) \
 = range(1,5)


# XnCMOSType enum
(XN_CMOS_TYPE_IMAGE, \
 XN_CMOS_TYPE_DEPTH, \
 XN_CMOS_COUNT) \
 = range(3)



# XnOSSeekType;
(XN_OS_SEEK_SET, \
 XN_OS_SEEK_CUR, \
 XN_OS_SEEK_END)\
 = range(3)




NI_LOG_DIR_NAME =          "Log"
NI_LOG_MASKS_STRING_LEN =  600
NI_MASK_LOG =              "Log"
NI_LOG_MASK_ALL =          "ALL"

NI_STATUS_OK = 0

NI_MAX_NAME_LENGTH = 80
NI_MAX_LICENSE_LENGTH = 255

def XN_CODEC_ID(c1,c2,c3,c4):
    return (ord(c4) << 24) | (ord(c3) << 16) | (ord(c2) << 8) | ord(c1)


#XN_CODEC_NULL = XN_CODEC_ID(0, 0, 0, 0)
XN_CODEC_UNCOMPRESSED = XN_CODEC_ID('N','O','N','E')
XN_CODEC_JPEG = XN_CODEC_ID('J','P','E','G')
XN_CODEC_16Z = XN_CODEC_ID('1','6','z','P')
XN_CODEC_16Z_EMB_TABLES = XN_CODEC_ID('1','6','z','T')
XN_CODEC_8Z = XN_CODEC_ID('I','m','8','z')



#XnPlayerSeekOrigin enum
(XN_PLAYER_SEEK_SET, \
 XN_PLAYER_SEEK_CUR, \
 XN_PLAYER_SEEK_END) \
= range(3)



class NiMapOutputMode(Structure):
    _fields_ = [("nXRes", c_uint32),
                ("nYRes", c_uint32),
                ("nFPS",  c_uint32)]


class NiWaveOutputMode(Structure):
    _fields_ = [("nSampleRate",    c_uint32),
                ("nBitsPerSample", c_uint16),
                ("nChannels",      c_uint8)]


class NiVersion(Structure):
    _fields_ = [("nMajor",       c_uint8),
                ("nMinor",       c_uint8),
                ("nMaintenance", c_uint16),
                ("nBuild",       c_uint32)]


class NiProductionNodeDescription(Structure):
    _fields_ = [("Type",       c_uint32),   #C++ enum
                ("strVendor",  c_char * NI_MAX_NAME_LENGTH),
                ("strName",    c_char * NI_MAX_NAME_LENGTH ),
                ("Version",    NiVersion)]


class NiLicense(Structure):
    _fields_ = [("strVendor",  c_char * NI_MAX_NAME_LENGTH),
                ("strKey",     c_char * NI_MAX_LICENSE_LENGTH )]


class NiCropping(Structure):
    _fields_ = [("bEnabled",    c_uint32),   #NiBool
                ("nXOffset",    c_uint16 ),
                ("nYOffset",    c_uint16 ),
                ("nXSize",      c_uint16 ),
                ("nYSize",      c_uint16 )]


class XnCmosBlankingTime(Structure):
    _fields_ = [("nCmosID",             c_uint32),   #C++ enum
                ("nTimeInMilliseconds", c_float),
                ("nNumberOfFrames",     c_uint16)]



class XnSDKVersion(Structure):
    _pack_      = 1
    _fields_ = [("nMajor",       c_uint8),
                ("nMinor",       c_uint8),
                ("nMaintenance", c_uint8),
                ("nBuild",       c_uint16)]


class XnVersions(Structure):
    _pack_      = 1
    _fields_ = [("nMajor",         c_uint8),
                ("nMinor",         c_uint8),
                ("nBuild",         c_uint16),
                ("nChip",          c_uint32),
                ("nFPGA",          c_uint16),
                ("nSystemVersion", c_uint16),
                ("SDK",            XnSDKVersion),
                ("XnHWVer",        c_uint32),     #c++ enum
                ("XnFWVer",        c_uint32),     #c++ enum
                ("XnSensorVer",    c_uint32),     #c++ enum
                ("XnChipVer",      c_uint32)]     #c++ enum

class XnNodeInfoListIterator(Structure):
    _pack_      = 1
    _fields_ = [("pCurrent",      c_void_p)]


class NiDevice(object):
    def __init__(self):

        self.ni_contexts = []

        self.depth_nodes = []
        self.ir_nodes = []
        self.image_nodes = []
        self.audio_nodes = []
        self.device_nodes = []
        self.player_nodes =[]


        # NITE
        self.gesture_nodes = []
        self.scene_nodes = []
        self.hands_nodes = []
        self.user_nodes = []

        # 'node' or 'any' or 'all'
        self.primary_stream_state = 'any'
        self.primary_stream_node = 0



XN_MODULE_PROPERTY_USB_INTERFACE =         "UsbInterface"
XN_STREAM_PROPERTY_INPUT_FORMAT =          "InputFormat"
XN_STREAM_PROPERTY_OUTPUT_FORMAT =         "OutputFormat"
XN_MODULE_PROPERTY_RESET =                 "Reset"
XN_MODULE_PROPERTY_FRAME_SYNC =            "FrameSync"
XN_STREAM_PROPERTY_REQUIRED_DATA_SIZE =    "RequiredDataSize"
XN_STREAM_PROPERTY_GMC_MODE =              "GmcMode"
XN_MODULE_PROPERTY_CMOS_BLANKING_TIME =    "CmosBlankingTime"


XN_STREAM_PROPERTY_GAIN =                  "Gain"
XN_STREAM_PROPERTY_HOLE_FILTER =           "HoleFilter"
XN_STREAM_PROPERTY_MIN_DEPTH =             "MinDepthValue"
XN_STREAM_PROPERTY_MAX_DEPTH =             "MaxDepthValue"
XN_STREAM_PROPERTY_REGISTRATION =          "Registration"
XN_STREAM_PROPERTY_WHITE_BALANCE_ENABLED = "WhiteBalancedEnabled"
XN_STREAM_PROPERTY_FLICKER =               "Flicker"
XN_MODULE_PROPERTY_PRIMARY_STREAM =        "PrimaryStream"


XN_MODULE_PROPERTY_VERSION =               "Version"
XN_MODULE_PROPERTY_ID =                    "ID"


########################################
#### Definition of the return types ####
########################################

cli.xnInit.restype = c_int
cli.xnLogInitSystem.restype = c_int
cli.xnLogSetConsoleOutput.restype = c_int
cli.xnLogSetFileOutput.restype = c_int
cli.xnLogSetMaskState.restype = c_int
cli.xnLogSetSeverityFilter.restype = c_int
cli.xnLogClose.restype = c_int
cli.xnEnumerateProductionTrees.restype = c_int
cli.xnEnumerateExistingNodesByType.restype = c_int
cli.xnNodeInfoListGetFirst.restype = XnNodeInfoListIterator
cli.xnNodeInfoListGetNext.restype = XnNodeInfoListIterator
cli.xnNodeInfoListGetCurrent.restype = c_void_p
cli.xnCreateProductionTree.restype = c_int
#cli.xnCreateAnyProductionTree.restype = c_int
#cli.xnNodeInfoListFree .restype
cli.xnSetMapOutputMode.restype = c_int
cli.xnStartGeneratingAll.restype = c_int
cli.xnStartGenerating.restype = c_int
cli.xnStopGeneratingAll.restype = c_int
cli.xnGetMapOutputMode.restype = c_int
cli.xnWaitOneUpdateAll.restype = c_int
cli.xnWaitAnyUpdateAll.restype = c_int
cli.xnGetStatusString.restype = c_char_p
# xnGetIRMap and xnGetDepthMap actually returns uint16* but the prime sensor can change the output format
cli.xnGetIRMap.restype = c_void_p
cli.xnGetDepthMap.restype = c_void_p
cli.xnGetImageMap.restype = c_void_p
cli.xnGetRGB24ImageMap.restype = c_void_p
cli.xnGetFrameID.restype = c_uint
#cli.xnShutdown.restype
cli.xnSetPixelFormat.restype = c_int
cli.xnGetPixelFormat.restype = c_int
cli.xnSetIntProperty.restype = c_int
cli.xnSetRealProperty.restype = c_int
cli.xnSetStringProperty.restype = c_int
cli.xnSetGeneralProperty.restype = c_int
cli.xnGetIntProperty.restype = c_int
cli.xnGetRealProperty.restype = c_int
cli.xnGetStringProperty.restype = c_int
cli.xnGetGeneralProperty.restype = c_int
cli.xnSetWaveOutputMode.restype = c_int
cli.xnGetWaveOutputMode.restype = c_int
cli.xnGetDataSize.restype = c_int
cli.xnGetTimestamp.restype = c_ulonglong
cli.xnNodeInfoGetDescription.restype = c_void_p
cli.xnGetNodeInfo.restype = c_void_p
cli.xnGetAudioBuffer.restype = c_void_p
cli.xnIsNewDataAvailable.restype = c_char
cli.xnSetViewPoint.restype = c_int
cli.xnSetCropping.restype = c_int
cli.xnGetCropping.restype = c_int
cli.xnIsGenerating.restype = c_int
cli.xnWaitAndUpdateData.restype = c_int
cli.xnIsDataNew.restype = c_int
cli.xnIsGenerating.restype = c_int
cli.xnAddLicense.restype = c_int
cli.xnFrameSyncWith.restype = c_int
cli.xnIsFrameSyncedWith.restype = c_int
cli.xnContextOpenFileRecording.restype = c_int
cli.xnNodeInfoGetHandle.restype = c_void_p
cli.xnNodeInfoListIteratorIsValid.restype = c_int
#cli.xnUnrefProductionNode.restype
#cli.xnNodeInfoListGetNext.restype = c_void_p
#cli.xnGetVersion.restype
cli.xnSetRecorderDestination.restype = c_int
cli.xnAddNodeToRecording.restype = c_int
cli.xnRemoveNodeFromRecording.restype = c_int
cli.xnRecord.restype = c_int
cli.xnSeekPlayerToTimeStamp.restype = c_int
cli.xnSeekPlayerToFrame.restype = c_int
cli.xnTellPlayerFrame.restype = c_int
cli.xnGetPlayerNumFrames.restype = c_int
cli.xnGetPlayerSupportedFormat.restype = c_char_p
cli.xnEnumeratePlayerNodes.restype = c_int
cli.xnIsPlayerAtEOF.restype = c_int
cli.xnGetNodeName.restype = c_char_p
cli.xnFindExistingNodeByType.restype = c_int
cli.xnSetMirror.restype = c_int
cli.xnStopFrameSyncWith.restype = c_int
cli.xnResetViewPoint.restype = c_int

cli.xnNodeInfoGetCreationInfo.restype = c_char_p






# Register and unregister to callbacks
cli.xnRegisterToMapOutputModeChange.restype = c_int
#cli.xnUnregisterFromMapOutputModeChange.restype
cli.xnRegisterToWaveOutputModeChanges.restype = c_int
#cli.xnUnregisterFromWaveOutputModeChanges.restype
cli.xnRegisterToViewPointChange.restype = c_int
#cli.xnUnregisterFromViewPointChange.restype
cli.xnRegisterToMirrorChange.restype = c_int
#cli.xnUnregisterFromMirrorChange.restype
cli.xnRegisterToPixelFormatChange.restype = c_int
#cli.xnUnregisterFromPixelFormatChange.restype
cli.xnRegisterToNewDataAvailable.restype = c_int
#cli.xnUnregisterFromNewDataAvailable.restype
cli.xnRegisterToGenerationRunningChange.restype = c_int
#cli.xnUnregisterFromGenerationRunningChange.restype
cli.xnRegisterToFrameSyncChange.restype = c_int
#cli.xnUnregisterFromFrameSyncChange.restype
cli.xnRegisterToCroppingChange.restype = c_int
#cli.xnUnregisterFromCroppingChange.restype
cli.xnRegisterToGlobalErrorStateChange.restype = c_int
#cli.xnUnregisterFromGlobalErrorStateChange.restype



#########################################
###### Definition of the arguments ######
#########################################


cli.xnInit.argtypes = [POINTER(c_void_p)]
cli.xnLogInitSystem.argtypes = []
cli.xnLogSetConsoleOutput.argtypes = [c_int]
cli.xnLogSetFileOutput.argtypes = [c_int]
cli.xnLogSetMaskState.argtypes = [c_char_p,c_int]
cli.xnLogSetSeverityFilter.argtypes = [c_int]
cli.xnLogClose.argtypes = []
cli.xnEnumerateProductionTrees.argtypes = [c_void_p, c_int, c_void_p, POINTER(c_void_p),c_void_p]
cli.xnEnumerateExistingNodesByType.argtypes = [c_void_p, c_int, POINTER(c_void_p)]
cli.xnNodeInfoListGetFirst.argtypes = [c_void_p]
cli.xnNodeInfoListGetCurrent.argtypes = [XnNodeInfoListIterator]
cli.xnCreateProductionTree.argtypes = [c_void_p, c_void_p, POINTER(c_void_p)]
#cli.xnCreateAnyProductionTree.argtypes = [c_void_p, c_void_p, POINTER(c_void_p)]
cli.xnNodeInfoListFree .argtypes = [c_void_p]
cli.xnSetMapOutputMode.argtypes = [c_void_p, c_void_p]
cli.xnStartGeneratingAll.argtypes = [c_void_p]
cli.xnStartGenerating.argtypes = [c_void_p]
cli.xnStopGeneratingAll.argtypes = [c_void_p]
cli.xnGetMapOutputMode.argtypes = [c_void_p, c_void_p]
cli.xnWaitOneUpdateAll.argtypes = [c_void_p, c_void_p]
cli.xnWaitAnyUpdateAll.argtypes = [c_void_p]
cli.xnGetStatusString.argtypes = [c_int]
cli.xnGetIRMap.argtypes = [c_void_p]
cli.xnGetDepthMap.argtypes = [c_void_p]
cli.xnGetImageMap.argtypes = [c_void_p]
cli.xnGetRGB24ImageMap.argtypes = [c_void_p]
cli.xnGetFrameID.argtypes = [c_void_p]
cli.xnShutdown.argtypes = [c_void_p]
cli.xnSetPixelFormat.argtypes = [c_void_p, c_int]
cli.xnGetPixelFormat.argtypes = [c_void_p]
cli.xnSetIntProperty.argtypes = [c_void_p, c_char_p,  c_ulonglong]
cli.xnSetRealProperty.argtypes = [c_void_p, c_char_p,  c_double]
cli.xnSetStringProperty.argtypes = [c_void_p, c_char_p,  c_char_p]
cli.xnSetGeneralProperty.argtypes = [c_void_p, c_char_p, c_uint, c_void_p]
cli.xnGetIntProperty.argtypes = [c_void_p, c_char_p, POINTER(c_ulonglong)]
cli.xnGetRealProperty.argtypes = [c_void_p, c_char_p, POINTER(c_double)]
cli.xnGetStringProperty.argtypes = [c_void_p, c_char_p, c_char_p]
cli.xnGetGeneralProperty.argtypes = [c_void_p, c_char_p,c_uint, c_void_p]
cli.xnSetWaveOutputMode.argtypes = [c_void_p, c_void_p]
cli.xnGetWaveOutputMode.argtypes = [c_void_p, c_void_p]
cli.xnGetDataSize.argtypes = [c_void_p]
cli.xnGetTimestamp.argtypes = [c_void_p]
cli.xnGetFrameID.argtypes = [c_void_p]
cli.xnNodeInfoGetDescription.argtypes = [c_void_p]
###
cli.xnNodeInfoGetCreationInfo.argtypes = [c_void_p]
cli.xnNodeInfoListGetNext.argstypes = [XnNodeInfoListIterator]

###
cli.xnGetNodeInfo.argtypes = [c_void_p]
cli.xnGetAudioBuffer.argtypes = [c_void_p]
cli.xnIsNewDataAvailable.argtypes = [c_void_p]
cli.xnSetViewPoint.argtypes = [c_void_p, c_void_p]
cli.xnSetCropping.argtypes = [c_void_p, c_void_p]
cli.xnGetCropping.argtypes = [c_void_p, c_void_p]
cli.xnIsGenerating.argtypes = [c_void_p]
cli.xnWaitAndUpdateData.argtypes = [c_void_p]
cli.xnIsDataNew.argtypes = [c_void_p]
cli.xnIsGenerating.argtypes = [c_void_p]
cli.xnAddLicense.argtypes = [c_void_p, c_void_p]
cli.xnFrameSyncWith.argtypes = [c_void_p, c_void_p]
cli.xnIsFrameSyncedWith.argtypes = [c_void_p,c_void_p]
cli.xnContextOpenFileRecording.argtypes = [c_void_p, c_char_p]
cli.xnNodeInfoGetHandle.argtypes = [c_void_p]
cli.xnNodeInfoListIteratorIsValid.argtypes = [XnNodeInfoListIterator]
cli.xnUnrefProductionNode.argtypes = [c_void_p]
#cli.xnNodeInfoListGetNext.argtypes = [c_void_p]
cli.xnGetVersion.argtypes = [c_void_p]
cli.xnSetRecorderDestination.argtypes = [c_void_p, c_int, c_char_p]
cli.xnAddNodeToRecording.argtypes = [c_void_p, c_void_p, c_int];
cli.xnRemoveNodeFromRecording.argtypes = [c_void_p, c_void_p]
cli.xnRecord.argtypes = [c_void_p]
cli.xnSeekPlayerToTimeStamp.argtypes = [c_void_p, c_long, c_int]
cli.xnSeekPlayerToFrame.argtypes = [c_void_p, c_char_p, c_int, c_int]
cli.xnTellPlayerFrame.argtypes = [c_void_p, c_char_p, POINTER(c_int)]
cli.xnGetPlayerNumFrames.argtypes = [c_void_p, c_char_p, POINTER(c_int)]
cli.xnGetPlayerSupportedFormat.argtypes = [c_void_p]
cli.xnEnumeratePlayerNodes.argtypes = [c_void_p, POINTER(c_void_p)]
cli.xnIsPlayerAtEOF.argtypes = [c_void_p]
cli.xnGetNodeName.argtypes = [c_void_p]
cli.xnFindExistingNodeByType.argstypes = [c_void_p,c_uint,POINTER(c_void_p)]
cli.xnSetMirror.argstypes = [c_void_p,c_int]

cli.xnStopFrameSyncWith.argstypes = [c_void_p,c_void_p]
cli.xnResetViewPoint.argstypes = [c_void_p]







# Register and unregister to callbacks
cli.xnRegisterToMapOutputModeChange.argstypes = [c_void_p, c_void_p, c_void_p, c_void_p]
cli.xnUnregisterFromMapOutputModeChange.argstypes = [c_void_p,c_void_p]
cli.xnRegisterToWaveOutputModeChanges.argstypes = [c_void_p, c_void_p, c_void_p, c_void_p]
cli.xnUnregisterFromWaveOutputModeChanges.argstypes = [c_void_p,c_void_p]
cli.xnRegisterToViewPointChange.argstypes = [c_void_p, c_void_p, c_void_p, c_void_p]
cli.xnUnregisterFromViewPointChange.argstypes = [c_void_p,c_void_p]
cli.xnRegisterToMirrorChange.argstypes = [c_void_p, c_void_p, c_void_p, c_void_p]
cli.xnUnregisterFromMirrorChange.argstypes = [c_void_p,c_void_p]
cli.xnRegisterToPixelFormatChange.argstypes = [c_void_p, c_void_p, c_void_p, c_void_p]
cli.xnUnregisterFromPixelFormatChange.argstypes = [c_void_p,c_void_p]
cli.xnRegisterToNewDataAvailable.argstypes = [c_void_p, c_void_p, c_void_p, c_void_p]
cli.xnUnregisterFromNewDataAvailable.argstypes = [c_void_p,c_void_p]
cli.xnRegisterToGenerationRunningChange.argstypes = [c_void_p, c_void_p, c_void_p, c_void_p]
cli.xnUnregisterFromGenerationRunningChange.argstypes = [c_void_p,c_void_p]
cli.xnRegisterToFrameSyncChange.argstypes = [c_void_p, c_void_p, c_void_p, c_void_p]
cli.xnUnregisterFromFrameSyncChange.argstypes = [c_void_p,c_void_p]
cli.xnRegisterToCroppingChange.argstypes = [c_void_p, c_void_p, c_void_p, c_void_p]
cli.xnUnregisterFromCroppingChange.argstypes = [c_void_p,c_void_p]
cli.xnRegisterToGlobalErrorStateChange.argstypes = [c_void_p, c_void_p, c_void_p, c_void_p]
cli.xnUnregisterFromGlobalErrorStateChange.argstypes = [c_void_p,c_void_p]












NIPsVars = vars()


### ALTERNATIVE FOR WRAPPER FUNCTION ###
#def niInit(*args):
#    WriteLog('%s(%s)' %(sys._getframe().f_code.co_name,args))
#    ret_val = cli.xnInit(args)
#    WriteLog('%s return value: %s' % (sys._getframe().f_code.co_name, ret_val))
#    return ret_val
### ALTERNATIVE FOR WRAPPER FUNCTION ###


def niInit(ppContext):
    WriteLog('niInit(%s)' % (ppContext))
    ret_val = cli.xnInit(ppContext)
    WriteLog('niInit return value: %s' % (ret_val))
    return ret_val


def niLogInitSystem():
    WriteLog('niLogInitSystem()')
    ret_val = cli.xnLogInitSystem()
    WriteLog('niLogInitSystem return value: %s' % (ret_val))
    return ret_val


def niLogSetConsoleOutput(bConsoleOutput):
    WriteLog('niLogSetConsoleOutput(%s)' % (bConsoleOutput))
    ret_val = cli.xnLogSetConsoleOutput(bConsoleOutput)
    WriteLog('niLogSetConsoleOutput return value: %s' % (ret_val))
    return ret_val


def niLogSetFileOutput(bFileOutput):
    WriteLog('niLogSetFileOutput(%s)' % (bFileOutput))
    ret_val = cli.xnLogSetFileOutput(bFileOutput)
    WriteLog('niLogSetFileOutput return value: %s' % (ret_val))
    return ret_val


def niLogSetMaskState(csMask, bEnabled):
    WriteLog('niLogSetMaskState(%s, %s)' % (csMask, bEnabled))
    ret_val = cli.xnLogSetMaskState(csMask, bEnabled)
    WriteLog('niLogSetMaskState return value: %s' % (ret_val))
    return ret_val


def niLogSetSeverityFilter(nMinSeverity):
    WriteLog('niLogSetSeverityFilter(%s)' % (nMinSeverity))
    ret_val = cli.xnLogSetSeverityFilter(nMinSeverity)
    WriteLog('niLogSetSeverityFilter return value: %s' % (ret_val))
    return ret_val


def niLogClose():
    WriteLog('niLogClose()')
    ret_val = cli.xnLogClose()
    WriteLog('niLogClose return value: %s' % (ret_val))
    return ret_val


def niEnumerateProductionTrees(pContext, Type, pQuery, ppTreesList):
    WriteLog('niEnumerateProductionTrees(%s, %s, %s, %s)' % (pContext, Type, pQuery, ppTreesList))
    ret_val = cli.xnEnumerateProductionTrees(pContext, Type, pQuery, ppTreesList, 0)
    WriteLog('niEnumerateProductionTrees return value: %s' % (ret_val))
    return ret_val


def niEnumerateExistingNodesByType(pContext, Type, ppList):
    WriteLog('niEnumerateExistingNodesByType(%s, %s, %s)' % (pContext, Type, ppList))
    ret_val = cli.xnEnumerateExistingNodesByType(pContext, Type, ppList)
    WriteLog('niEnumerateExistingNodesByType return value: %s' % (ret_val))
    return ret_val


def niNodeInfoListGetFirst(pList):
    WriteLog('niNodeInfoListGetFirst(%s)' % (pList))
    ret_val = cli.xnNodeInfoListGetFirst(pList)
    WriteLog('niNodeInfoListGetFirst return value: %s' % (ret_val))
    return ret_val


def niNodeInfoListGetCurrent(pIt):
    WriteLog('niNodeInfoListGetCurrent(%s)' % (pIt))
    ret_val = cli.xnNodeInfoListGetCurrent(pIt)
    WriteLog('niNodeInfoListGetCurrent return value: %s' % (ret_val))
    return ret_val


def niCreateProductionTree(pContext, pTree, phNode):
    WriteLog('niCreateProductionTree(%s, %s, %s)' % (pContext, pTree, phNode))
    ret_val = cli.xnCreateProductionTree(pContext, pTree, phNode)
    WriteLog('niCreateProductionTree return value: %s' % (ret_val))
    return ret_val


def niNodeInfoListFree (pList):
    WriteLog('niNodeInfoListFree (%s)' % (pList))
    ret_val = cli.xnNodeInfoListFree (pList)
    # niNodeInfoListFree returns void
    # WriteLog('niNodeInfoListFree  return value: %s' % (ret_val))
    return ret_val


def niSetMapOutputMode(hInstance, pOutputMode):
    WriteLog('niSetMapOutputMode(%s, %s)' % (hInstance, pOutputMode))
    ret_val = cli.xnSetMapOutputMode(hInstance, pOutputMode)
    WriteLog('niSetMapOutputMode return value: %s' % (ret_val))
    return ret_val


def niStartGeneratingAll(pContext):
    WriteLog('niStartGeneratingAll(%s)' % (pContext))
    ret_val = cli.xnStartGeneratingAll(pContext)
    WriteLog('niStartGeneratingAll return value: %s' % (ret_val))
    return ret_val


def niStartGenerating(hInstance):
    WriteLog('niStartGenerating(%s)' % (hInstance))
    ret_val = cli.xnStartGenerating(hInstance)
    WriteLog('niStartGenerating return value: %s' % (ret_val))
    return ret_val


def niStopGeneratingAll(pContext):
    WriteLog('niStopGeneratingAll(%s)' % (pContext))
    ret_val = cli.xnStopGeneratingAll(pContext)
    WriteLog('niStopGeneratingAll return value: %s' % (ret_val))
    return ret_val


def niGetMapOutputMode(hInstance, pOutputMode):
    WriteLog('niGetMapOutputMode(%s, %s)' % (hInstance, pOutputMode))
    ret_val = cli.xnGetMapOutputMode(hInstance, pOutputMode)
    WriteLog('niGetMapOutputMode return value: %s' % (ret_val))
    return ret_val

#### Wait functions ####

def niWaitOneUpdateAll(pContext, hNode):
    WriteLog('niWaitOneUpdateAll(%s, %s)' % (pContext, hNode))
    ret_val = cli.xnWaitOneUpdateAll(pContext, hNode)
    WriteLog('niWaitOneUpdateAll return value: %s' % (ret_val))
    return ret_val


def niWaitAnyUpdateAll(pContext):
    WriteLog('niWaitAnyUpdateAll(%s)' % (pContext))
    ret_val = cli.xnWaitAnyUpdateAll(pContext)
    WriteLog('niWaitAnyUpdateAll return value: %s' % (ret_val))
    return ret_val


def niWaitAndUpdateData(hInstance):
    WriteLog('niWaitAndUpdateData(%s)' % (hInstance))
    ret_val = cli.xnWaitAndUpdateData(hInstance)
    WriteLog('niWaitAndUpdateData return value: %s' % (ret_val))
    return ret_val


def niGetStatusString(Status):
    WriteLog('niGetStatusString(%s)' % (Status))
    ret_val = cli.xnGetStatusString(Status)
    WriteLog('niGetStatusString return value: %s' % (ret_val))
    return ret_val


def niGetIRMap(hInstance):
    WriteLog('niGetIRMap(%s)' % (hInstance))
    ret_val = cli.xnGetIRMap(hInstance)
    WriteLog('niGetIRMap return value: %s' % (ret_val))
    return ret_val


def niGetDepthMap(hInstance):
    WriteLog('niGetDepthMap(%s)' % (hInstance))
    ret_val = cli.xnGetDepthMap(hInstance)
    WriteLog('niGetDepthMap return value: %s' % (ret_val))
    return ret_val


def niGetImageMap(hInstance):
    WriteLog('niGetImageMap(%s)' % (hInstance))
    ret_val = cli.xnGetImageMap(hInstance)
    WriteLog('niGetImageMap return value: %s' % (ret_val))
    return ret_val


def niGetRGB24ImageMap(hInstance):
    WriteLog('niGetRGB24ImageMap(%s)' % (hInstance))
    ret_val = cli.xnGetRGB24ImageMap(hInstance)
    WriteLog('niGetRGB24ImageMap return value: %s' % (ret_val))
    return ret_val


def niGetFrameID(hInstance):
    WriteLog('niGetFrameID(%s)' % (hInstance))
    ret_val = cli.xnGetFrameID(hInstance)
    WriteLog('niGetFrameID return value: %s' % (ret_val))
    return ret_val


def niShutdown(pContext):
    WriteLog('niShutdown(%s)' % (pContext))
    ret_val = cli.xnShutdown(pContext)
    # niShutdown returns void
    # WriteLog('niShutdown return value: %s' % (ret_val))
    return ret_val


def niSetPixelFormat(hInstance, Format):
    WriteLog('niSetPixelFormat(%s, %s)' % (hInstance, Format))
    ret_val = cli.xnSetPixelFormat(hInstance, Format)
    WriteLog('niSetPixelFormat return value: %s' % (ret_val))
    return ret_val



def niGetPixelFormat(hInstance):
    WriteLog('niGetPixelFormat(%s)' % (hInstance))
    ret_val = cli.xnGetPixelFormat(hInstance)
    WriteLog('niGetPixelFormat return value: %s' % (ret_val))
    return ret_val



def niSetIntProperty(hInstance, strName, nValue):
    WriteLog('niSetIntProperty(%s, %s, %s)' % (hInstance, strName, nValue))
    ret_val = cli.xnSetIntProperty(hInstance, strName, nValue)
    WriteLog('niSetIntProperty return value: %s' % (ret_val))
    return ret_val


def niSetRealProperty(hInstance, strName, dValue):
    WriteLog('niSetRealProperty(%s, %s, %s)' % (hInstance, strName, dValue))
    ret_val = cli.xnSetRealProperty(hInstance, strName, dValue)
    WriteLog('niSetRealProperty return value: %s' % (ret_val))
    return ret_val


def niSetStringProperty(hInstance, strName, strValue):
    WriteLog('niSetStringProperty(%s, %s, %s)' % (hInstance, strName, strValue))
    ret_val = cli.xnSetStringProperty(hInstance, strName, strValue)
    WriteLog('niSetStringProperty return value: %s' % (ret_val))
    return ret_val


def niSetGeneralProperty(hInstance, strName, nBufferSize, pBuffer ):
    WriteLog('niSetGeneralProperty(%s, %s, %s, %s)' % (hInstance, strName, nBufferSize, pBuffer ))
    ret_val = cli.xnSetGeneralProperty(hInstance, strName, nBufferSize, pBuffer )
    WriteLog('niSetGeneralProperty return value: %s' % (ret_val))
    return ret_val


def niGetIntProperty(hInstance, strName, pnValue):
    value = c_ulonglong(0)
    value_ptr = pointer(value)
    WriteLog('niGetIntProperty(%s, %s, %s)' % (hInstance, strName, value_ptr))
    ret_val = cli.xnGetIntProperty(hInstance, strName, value_ptr)
    WriteLog('niGetIntProperty return value: %s' % (ret_val))
    pnValue[0] = value.value
    return ret_val


def niGetRealProperty(hInstance, strName, pdValue):
    WriteLog('niGetRealProperty(%s, %s, %s)' % (hInstance, strName, pdValue))
    ret_val = cli.xnGetRealProperty(hInstance, strName, pdValue)
    WriteLog('niGetRealProperty return value: %s' % (ret_val))
    return ret_val


def niGetStringProperty(hInstance, strName, csValue):
    WriteLog('niGetStringProperty(%s, %s, %s)' % (hInstance, strName, csValue))
    ret_val = cli.xnGetStringProperty(hInstance, strName, csValue)
    WriteLog('niGetStringProperty return value: %s' % (ret_val))
    return ret_val


def niGetGeneralProperty(hInstance, strName,nBufferSize, pBuffer):
    WriteLog('niGetGeneralProperty(%s, %s, %s ,%s)' % (hInstance, strName,nBufferSize, pBuffer))
    ret_val = cli.xnGetGeneralProperty(hInstance, strName,nBufferSize, pBuffer)
    WriteLog('niGetGeneralProperty return value: %s' % (ret_val))
    return ret_val


def niSetWaveOutputMode(hInstance, OutputMode):
    WriteLog('niSetWaveOutputMode(%s, %s)' % (hInstance, OutputMode))
    ret_val = cli.xnSetWaveOutputMode(hInstance, OutputMode)
    WriteLog('niSetWaveOutputMode return value: %s' % (ret_val))
    return ret_val


def niGetWaveOutputMode(hInstance, OutputMode):
    WriteLog('niGetWaveOutputMode(%s, %s)' % (hInstance, OutputMode))
    ret_val = cli.xnGetWaveOutputMode(hInstance, OutputMode)
    WriteLog('niGetWaveOutputMode return value: %s' % (ret_val))
    return ret_val


def niGetDataSize(hInstance):
    WriteLog('niGetDataSize(%s)' % (hInstance))
    ret_val = cli.xnGetDataSize(hInstance)
    WriteLog('niGetDataSize return value: %s' % (ret_val))
    return ret_val


def niGetTimestamp(hInstance):
    WriteLog('niGetTimestamp(%s)' % (hInstance))
    ret_val = cli.xnGetTimestamp(hInstance)
    WriteLog('niGetTimestamp return value: %s' % (ret_val))
    return ret_val


def niGetFrameID(hInstance):
    WriteLog('niGetFrameID(%s)' % (hInstance))
    ret_val = cli.xnGetFrameID(hInstance)
    WriteLog('niGetFrameID return value: %s' % (ret_val))
    return ret_val


def niNodeInfoGetDescription(pNodeInfo):
    WriteLog('niNodeInfoGetDescription(%s)' % (pNodeInfo))
    ret_val = cli.xnNodeInfoGetDescription(pNodeInfo)
    WriteLog('niNodeInfoGetDescription return value: %s' % (ret_val))
    return ret_val


def niNodeInfoGetCreationInfo(pNodeInfo):
    WriteLog('niNodeInfoGetCreationInfo(%s)' % (pNodeInfo))
    ret_val = cli.xnNodeInfoGetCreationInfo(pNodeInfo)
    WriteLog('niNodeInfoGetCreationInfo return value: %s' % (ret_val))
    return ret_val

def niGetNodeInfo(hNode):
    WriteLog('niGetNodeInfo(%s)' % (hNode))
    ret_val = cli.xnGetNodeInfo(hNode)
    WriteLog('niGetNodeInfo return value: %s' % (ret_val))
    return ret_val


def niGetAudioBuffer(hInstance):
    WriteLog('niGetAudioBuffer(%s)' % (hInstance))
    ret_val = cli.xnGetAudioBuffer(hInstance)
    WriteLog('niGetAudioBuffer return value: %s' % (ret_val))
    return ret_val


def niIsNewDataAvailable(hInstance):
    WriteLog('niIsNewDataAvailable(%s)' % (hInstance))
    ret_val = cli.xnIsNewDataAvailable(hInstance)
    WriteLog('niIsNewDataAvailable return value: %s' % (ret_val))
    return ret_val


def niSetViewPoint(hInstance, hOther):
    WriteLog('niSetViewPoint(%s, %s)' % (hInstance, hOther))
    ret_val = cli.xnSetViewPoint(hInstance, hOther)
    WriteLog('niSetViewPoint return value: %s' % (ret_val))
    return ret_val


def niSetCropping(hInstance, pCropping):
    WriteLog('niSetCropping(%s, %s)' % (hInstance, pCropping))
    ret_val = cli.xnSetCropping(hInstance, pCropping)
    WriteLog('niSetCropping return value: %s' % (ret_val))
    return ret_val


def niGetCropping(hInstance, pCropping):
    WriteLog('niGetCropping(%s, %s)' % (hInstance, pCropping))
    ret_val = cli.xnGetCropping(hInstance, pCropping)
    WriteLog('niGetCropping return value: %s' % (ret_val))
    return ret_val


def niIsGenerating(hInstance):
    WriteLog('niIsGenerating(%s)' % (hInstance))
    ret_val = cli.xnIsGenerating(hInstance)
    WriteLog('niIsGenerating return value: %s' % (ret_val))
    return ret_val





def niIsDataNew(hInstance):
    WriteLog('niIsDataNew(%s)' % (hInstance))
    ret_val = cli.xnIsDataNew(hInstance)
    WriteLog('niIsDataNew return value: %s' % (ret_val))
    return ret_val


def niIsGenerating(hInstance):
    WriteLog('niIsGenerating(%s)' % (hInstance))
    ret_val = cli.xnIsGenerating(hInstance)
    WriteLog('niIsGenerating return value: %s' % (ret_val))
    return ret_val


def niAddLicense(pContext, pLicense):
    WriteLog('niAddLicense(%s, %s)' % (pContext, pLicense))
    ret_val = cli.xnAddLicense(pContext, pLicense)
    WriteLog('niAddLicense return value: %s' % (ret_val))
    return ret_val


def niFrameSyncWith(hInstance, hOther):
    WriteLog('niFrameSyncWith(%s, %s)' % (hInstance, hOther))
    ret_val = cli.xnFrameSyncWith(hInstance, hOther)
    WriteLog('niFrameSyncWith return value: %s' % (ret_val))
    return ret_val


def niIsFrameSyncedWith(hInstance, hOther):
    WriteLog('niIsFrameSyncedWith(%s, %s)' % (hInstance, hOther))
    ret_val = cli.xnIsFrameSyncedWith(hInstance, hOther)
    WriteLog('niIsFrameSyncedWith return value: %s' % (ret_val))
    return ret_val


def niContextOpenFileRecording(pContext, strFileName):
    WriteLog('niContextOpenFileRecording(%s, %s)' % (pContext, strFileName))
    ret_val = cli.xnContextOpenFileRecording(pContext, strFileName)
    WriteLog('niContextOpenFileRecording return value: %s' % (ret_val))
    return ret_val


def niNodeInfoGetHandle(pNodeInfo):
    WriteLog('niNodeInfoGetHandle(%s)' % (pNodeInfo))
    ret_val = cli.xnNodeInfoGetHandle(pNodeInfo)
    WriteLog('niNodeInfoGetHandle return value: %s' % (ret_val))
    return ret_val


def niNodeInfoListIteratorIsValid(it):
    WriteLog('niNodeInfoListIteratorIsValid(%s)' % (it))
    ret_val = cli.xnNodeInfoListIteratorIsValid(it)
    WriteLog('niNodeInfoListIteratorIsValid return value: %s' % (ret_val))
    return ret_val


def niUnrefProductionNode(hNode):
    WriteLog('niUnrefProductionNode(%s)' % (hNode))
    ret_val = cli.xnUnrefProductionNode(hNode)
    WriteLog('niUnrefProductionNode return value: %s' % (ret_val))
    return ret_val


def niNodeInfoListGetNext(it):
    WriteLog('niNodeInfoListGetNext(%s)' % (it))
    ret_val = cli.xnNodeInfoListGetNext(it)
    WriteLog('niNodeInfoListGetNext return value: %s' % (ret_val))
    return ret_val



def niGetVersion(pVersion):
    WriteLog('niGetVersion(%s)' % (pVersion))
    ret_val = cli.xnGetVersion(pVersion)
    WriteLog('niGetVersion return value: %s' % (ret_val))
    return ret_val



def niSetMirror(hInstance, bMirror):
    WriteLog('niSetMirror(%s, %s)' % (hInstance, bMirror))
    ret_val = cli.xnSetMirror(hInstance, bMirror)
    WriteLog('niSetMirror return value: %s' % (ret_val))
    return ret_val


def niStopFrameSyncWith(hInstance, hOther):
    WriteLog('niStopFrameSyncWith(%s, %s)' % (hInstance, hOther))
    ret_val = cli.xnStopFrameSyncWith(hInstance, hOther)
    WriteLog('niStopFrameSyncWith return value: %s' % (ret_val))
    return ret_val



def niResetViewPoint(hInstance):
    WriteLog('niResetViewPoint(%s)' % (hInstance))
    ret_val = cli.xnResetViewPoint(hInstance)
    WriteLog('niResetViewPoint return value: %s' % (ret_val))
    return ret_val



### Context register and unregister callback functions


def niRegisterToGlobalErrorStateChange(pContext,handler,pCookie,phCallback):
    WriteLog('niRegisterToGlobalErrorStateChange(%s,%s,%s,%s)' % (pContext,handler,pCookie,phCallback))
    ret_val = cli.xnRegisterToGlobalErrorStateChange(pContext,handler,pCookie,phCallback)
    WriteLog('niRegisterToGlobalErrorStateChange return value: %s' % (ret_val))
    return ret_val


def niUnregisterFromGlobalErrorStateChange(pContext,hCallback):
    WriteLog('niUnregisterFromGlobalErrorStateChange(%s,%s)' % (pContext,hCallback))
    ret_val = cli.xnUnregisterFromGlobalErrorStateChange(pContext,hCallback)
    WriteLog('niUnregisterFromGlobalErrorStateChange return value: %s' % (ret_val))
    return ret_val


### Node register and unregister callback functions


def niRegisterToMapOutputModeChange(hInstance,handler,pCookie,phCallback):
    WriteLog('niRegisterToMapOutputModeChange(%s,%s,%s,%s)' % (hInstance,handler,pCookie,phCallback))
    ret_val = cli.xnRegisterToMapOutputModeChange(hInstance,handler,pCookie,phCallback)
    WriteLog('niRegisterToMapOutputModeChange return value: %s' % (ret_val))
    return ret_val



def niUnregisterFromMapOutputModeChange(hInstance,hCallback):
    WriteLog('niUnregisterFromMapOutputModeChange(%s,%s)' % (hInstance,hCallback))
    ret_val = cli.xnUnregisterFromMapOutputModeChange(hInstance,hCallback)
    WriteLog('niUnregisterFromMapOutputModeChange return value: %s' % (ret_val))
    return ret_val



def niRegisterToWaveOutputModeChanges(hInstance,handler,pCookie,phCallback):
    WriteLog('niRegisterToWaveOutputModeChanges(%s,%s,%s,%s)' % (hInstance,handler,pCookie,phCallback))
    ret_val = cli.xnRegisterToWaveOutputModeChanges(hInstance,handler,pCookie,phCallback)
    WriteLog('niRegisterToWaveOutputModeChanges return value: %s' % (ret_val))
    return ret_val


def niUnregisterFromWaveOutputModeChanges(hInstance,hCallback):
    WriteLog('niUnregisterFromWaveOutputModeChanges(%s,%s)' % (hInstance,hCallback))
    ret_val = cli.xnUnregisterFromWaveOutputModeChanges(hInstance,hCallback)
    WriteLog('niUnregisterFromWaveOutputModeChanges return value: %s' % (ret_val))
    return ret_val


def niRegisterToViewPointChange(hInstance,handler,pCookie,phCallback):
    WriteLog('niRegisterToViewPointChange(%s,%s,%s,%s)' % (hInstance,handler,pCookie,phCallback))
    ret_val = cli.xnRegisterToViewPointChange(hInstance,handler,pCookie,phCallback)
    WriteLog('niRegisterToViewPointChange return value: %s' % (ret_val))
    return ret_val


def niUnregisterFromViewPointChange(hInstance,hCallback):
    WriteLog('niUnregisterFromViewPointChange(%s,%s)' % (hInstance,hCallback))
    ret_val = cli.xnUnregisterFromViewPointChange(hInstance,hCallback)
    WriteLog('niUnregisterFromViewPointChange return value: %s' % (ret_val))
    return ret_val


def niRegisterToMirrorChange(hInstance,handler,pCookie,phCallback):
    WriteLog('niRegisterToMirrorChange(%s,%s,%s,%s)' % (hInstance,handler,pCookie,phCallback))
    ret_val = cli.xnRegisterToMirrorChange(hInstance,handler,pCookie,phCallback)
    WriteLog('niRegisterToMirrorChange return value: %s' % (ret_val))
    return ret_val


def niUnregisterFromMirrorChange(hInstance,hCallback):
    WriteLog('niUnregisterFromMirrorChange(%s,%s)' % (hInstance,hCallback))
    ret_val = cli.xnUnregisterFromMirrorChange(hInstance,hCallback)
    WriteLog('niUnregisterFromMirrorChange return value: %s' % (ret_val))
    return ret_val


def niRegisterToCroppingChange(hInstance,handler,pCookie,phCallback):
    WriteLog('niRegisterToCroppingChange(%s,%s,%s,%s)' % (hInstance,handler,pCookie,phCallback))
    ret_val = cli.xnRegisterToCroppingChange(hInstance,handler,pCookie,phCallback)
    WriteLog('niRegisterToCroppingChange return value: %s' % (ret_val))
    return ret_val


def niUnregisterFromCroppingChange(hInstance,hCallback):
    WriteLog('niUnregisterFromCroppingChange(%s,%s)' % (hInstance,hCallback))
    ret_val = cli.xnUnregisterFromCroppingChange(hInstance,hCallback)
    WriteLog('niUnregisterFromCroppingChange return value: %s' % (ret_val))
    return ret_val


def niRegisterToFrameSyncChange(hInstance,handler,pCookie,phCallback):
    WriteLog('niRegisterToFrameSyncChange(%s,%s,%s,%s)' % (hInstance,handler,pCookie,phCallback))
    ret_val = cli.xnRegisterToFrameSyncChange(hInstance,handler,pCookie,phCallback)
    WriteLog('niRegisterToFrameSyncChange return value: %s' % (ret_val))
    return ret_val


def niUnregisterFromFrameSyncChange(hInstance,hCallback):
    WriteLog('niUnregisterFromFrameSyncChange(%s,%s)' % (hInstance,hCallback))
    ret_val = cli.xnUnregisterFromFrameSyncChange(hInstance,hCallback)
    WriteLog('niUnregisterFromFrameSyncChange return value: %s' % (ret_val))
    return ret_val


def niRegisterToGenerationRunningChange(hInstance,handler,pCookie,phCallback):
    WriteLog('niRegisterToGenerationRunningChange(%s,%s,%s,%s)' % (hInstance,handler,pCookie,phCallback))
    ret_val = cli.xnRegisterToGenerationRunningChange(hInstance,handler,pCookie,phCallback)
    WriteLog('niRegisterToGenerationRunningChange return value: %s' % (ret_val))
    return ret_val


def niUnregisterFromGenerationRunningChange(hInstance,hCallback):
    WriteLog('niUnregisterFromGenerationRunningChange(%s,%s)' % (hInstance,hCallback))
    ret_val = cli.xnUnregisterFromGenerationRunningChange(hInstance,hCallback)
    WriteLog('niUnregisterFromGenerationRunningChange return value: %s' % (ret_val))
    return ret_val


def niRegisterToNewDataAvailable(hInstance,handler,pCookie,phCallback):
    WriteLog('niRegisterToNewDataAvailable(%s,%s,%s,%s)' % (hInstance,handler,pCookie,phCallback))
    ret_val = cli.xnRegisterToNewDataAvailable(hInstance,handler,pCookie,phCallback)
    WriteLog('niRegisterToNewDataAvailable return value: %s' % (ret_val))
    return ret_val


def niUnregisterFromNewDataAvailable(hInstance,hCallback):
    WriteLog('niUnregisterFromNewDataAvailable(%s,%s)' % (hInstance,hCallback))
    ret_val = cli.xnUnregisterFromNewDataAvailable(hInstance,hCallback)
    WriteLog('niUnregisterFromNewDataAvailable return value: %s' % (ret_val))
    return ret_val


def niRegisterToPixelFormatChange(hInstance,handler,pCookie,phCallback):
    WriteLog('niRegisterToPixelFormatChange(%s,%s,%s,%s)' % (hInstance,handler,pCookie,phCallback))
    ret_val = cli.xnRegisterToPixelFormatChange(hInstance,handler,pCookie,phCallback)
    WriteLog('niRegisterToPixelFormatChange return value: %s' % (ret_val))
    return ret_val


def niUnregisterFromPixelFormatChange(hInstance,hCallback):
    WriteLog('niUnregisterFromPixelFormatChange(%s,%s)' % (hInstance,hCallback))
    ret_val = cli.xnUnregisterFromPixelFormatChange(hInstance,hCallback)
    WriteLog('niUnregisterFromPixelFormatChange return value: %s' % (ret_val))
    return ret_val


# TODO = DEBUG info#############################
def niSetRecorderDestination(hInstance,destType,strDest):
    WriteLog('niSetRecorderDestination(%s,%s,%s)' % (hInstance,destType,strDest))
    ret_val = cli.xnSetRecorderDestination(hInstance,destType,strDest)
    WriteLog('niSetRecorderDestination return value: %s' % (ret_val))
    return ret_val

def niAddNodeToRecording(hInstance,hNode,compression):
    WriteLog('niAddNodeToRecording(%s,%s,%s)' % (hInstance,hNode,compression))
    ret_val = cli.xnAddNodeToRecording(hInstance,hNode,compression)
    WriteLog('niAddNodeToRecording return value: %s' % (ret_val))
    return ret_val

def niRemoveNodeFromRecording(hInstance,hNode):
    WriteLog('niRemoveNodeFromRecording(%s,%s)' % (hInstance,hNode))
    ret_val = cli.xnRemoveNodeFromRecording(hInstance,hNode)
    WriteLog('niRemoveNodeFromRecording return value: %s' % (ret_val))
    return ret_val

def niRecord(hInstance):
    WriteLog('niRecord(%s)' % (hInstance))
    ret_val = cli.xnRecord(hInstance)
    WriteLog('niRecord return value: %s' % (ret_val))
    return ret_val


def niSeekPlayerToTimeStamp(hPlayer,nTimeOffset,origin):
    WriteLog('niSeekPlayerToTimeStamp(%s,%s,%s)' % (hPlayer,nTimeOffset,origin))
    ret_val = cli.xnSeekPlayerToTimeStamp(hPlayer,nTimeOffset,origin)
    WriteLog('niSeekPlayerToTimeStamp return value: %s' % (ret_val))
    return ret_val

def niSeekPlayerToFrame( hPlayer,strNodeName,nFrameOffset,origin):
    WriteLog('niSeekPlayerToFrame(%s,%s,%s,%s)' % ( hPlayer,strNodeName,nFrameOffset,origin))
    ret_val = cli.xnSeekPlayerToFrame(hPlayer,strNodeName,nFrameOffset,origin)
    WriteLog('niSeekPlayerToFrame return value: %s' % (ret_val))
    return ret_val

def niTellPlayerFrame(hPlayer,strNodeName,pnFrame):
    WriteLog('niTellPlayerFrame(%s,%s,%s)' % (hPlayer,strNodeName,pnFrame))
    ret_val = cli.xnTellPlayerFrame(hPlayer,strNodeName,pnFrame)
    WriteLog('niTellPlayerFrame return value: %s' % (ret_val))
    return ret_val

def niGetPlayerNumFrames(hPlayer,strNodeName,pnFrames):
    WriteLog('niGetPlayerNumFrames(%s,%s,%s)' % (hPlayer,strNodeName,pnFrames))
    ret_val = cli.xnGetPlayerNumFrames(hPlayer,strNodeName,pnFrames)
    WriteLog('niGetPlayerNumFrames return value: %s' % (ret_val))
    return ret_val

def niGetPlayerSupportedFormat(hPlayer):
    WriteLog('niGetPlayerSupportedFormat(%s)' % (hPlayer))
    ret_val = cli.xnGetPlayerSupportedFormat(hPlayer)
    WriteLog('niGetPlayerSupportedFormat return value: %s' % (ret_val))
    return ret_val

def niEnumeratePlayerNodes(hPlayer,ppList):
    WriteLog('niEnumeratePlayerNodes(%s,%s)' % (hPlayer,ppList))
    ret_val = cli.xnEnumeratePlayerNodes(hPlayer,ppList)
    WriteLog('niEnumeratePlayerNodes return value: %s' % (ret_val))
    return ret_val

def niIsPlayerAtEOF(hPlayer):
    WriteLog('niIsPlayerAtEOF(%s)' % (hPlayer))
    ret_val = cli.xnIsPlayerAtEOF(hPlayer)
    WriteLog('niIsPlayerAtEOF return value: %s' % (ret_val))
    return ret_val

def niGetNodeName(hNode):
    WriteLog('niGetNodeName(%s)' % (hNode))
    ret_val = cli.xnGetNodeName(hNode)
    WriteLog('niGetNodeName return value: %s' % (ret_val))
    return ret_val


def niFindExistingNodeByType(pContext,type,phNode):
    WriteLog('niFindExistingNodeByType(%s,%s,%s)' % (pContext,type,phNode))
    ret_val = cli.xnFindExistingNodeByType(pContext,type,phNode)
    WriteLog('niFindExistingNodeByType return value: %s' % (ret_val))
    return ret_val



# TODO = DEBUG info#############################





#### utility functions


def NI_LogInit():
    niLogInitSystem()
    niLogSetConsoleOutput(1)
    niLogSetFileOutput(1)
    niLogSetMaskState(NI_LOG_MASK_ALL, 1)
    niLogSetSeverityFilter(NI_LOG_VERBOSE)



def NI_LogClose():
    niLogClose()



def NI_GetNodeTypeFromNodeHandle(node_handle):
    node_info = niGetNodeInfo(node_handle)
    node_description = niNodeInfoGetDescription(node_info)
    description_ptr = cast(node_description,POINTER(NiProductionNodeDescription))
    return description_ptr.contents.Type


def NI_GetPropertyValueFromString(property_str):
    return NIPsVars[property_str]


def NI_OSmemcpy(destination,source,size):
    if sys.platform == 'win32':
        cdll.msvcrt.memcpy(destination,source,size)
    else:
        libc.memcpy(destination,source,size)
