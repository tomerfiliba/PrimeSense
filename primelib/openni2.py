import os
import ctypes
import weakref
from primelib import _openni2 as oni
from primelib.utils import inherit_properties, HandleObject, _py_to_ctype_obj, ClosedHandle


def initialize(dll_directory = "."):
    prev = os.getcwd()
    os.chdir(dll_directory)
    oni.load_dll("OpenNI2")
    oni.oniInitialize(oni.ONI_API_VERSION)
    os.chdir(prev)

def unload():
    oni.oniShutdown()

def get_version():
    return oni.oniGetVersion()

def enumerate_devices():
    pdevs = ctypes.POINTER(oni.OniDeviceInfo)()
    count = ctypes.c_int()
    oni.oniGetDeviceList(ctypes.byref(pdevs), ctypes.byref(count))
    devices = [oni.OniDeviceInfo(pdevs[i]) for i in range(count.value)]
    oni.oniReleaseDeviceList(pdevs)
    return devices

def wait_for_any_stream(streams, timeout = None):
    if timeout is None:
        timeout = oni.ONI_TIMEOUT_FOREVER
    ready_stream_index = ctypes.c_int(-1)
    arr = (oni.OniStreamHandle * len(streams))()
    for i, s in enumerate(streams):
        arr[i] = s._handle
    oni.oniWaitForAnyStream(arr, len(streams), ctypes.byref(ready_stream_index), timeout)
    if ready_stream_index.value >= 0:
        return streams[ready_stream_index]
    else:
        return None

VideoMode = oni.OniVideoMode
DeviceInfo = oni.OniDeviceInfo

class SensorInfo(object):
    def __init__(self, info):
        self.sensorType = info.sensorType
        self.videoModes = [info.pSupportedVideoModes[i] for i in range(info.numSupportedVideoModes)]
    @classmethod
    def from_stream_handle(cls, handle):
        pinfo = oni.oniStreamGetSensorInfo(handle)
        if pinfo == 0:
            return None
        return cls(pinfo[0])
    @classmethod
    def from_device_handle(cls, handle, sensor_type):
        pinfo = oni.oniDeviceGetSensorInfo(handle, sensor_type)
        if pinfo == 0:
            return None
        return cls(pinfo[0])

class PlaybackSupport(object):
    __slots__ = ["device"]
    def __init__(self, device):
        self.device = weakref.proxy(device)
    def get_speed(self):
        return self.device.get_property(oni.ONI_DEVICE_PROPERTY_PLAYBACK_SPEED, ctypes.c_float)
    def set_speed(self, speed):
        return self.device.set_property(oni.ONI_DEVICE_PROPERTY_PLAYBACK_SPEED, speed)
    speed = property(get_speed, set_speed)

    def get_repeat_enabled(self):
        return bool(self.device.get_property(oni.ONI_DEVICE_PROPERTY_PLAYBACK_REPEAT_ENABLED, oni.OniBool))
    def set_repeat_enabled(self, enable):
        self.device.set_property(oni.ONI_DEVICE_PROPERTY_PLAYBACK_REPEAT_ENABLED, oni.OniBool)
    repeat = property(get_repeat_enabled, set_repeat_enabled)

    def seek(self, stream, frame_index):
        seek = oni.OniSeek(frameIndex = frame_index, stream = stream._handle)
        self.device.invoke(oni.ONI_DEVICE_COMMAND_SEEK, seek)
    def get_number_of_frames(self, stream):
        return stream.get_number_of_frames()

class Device(HandleObject):
    def __init__(self, uri):
        self.uri = uri
        handle = oni.OniDeviceHandle()
        oni.oniDeviceOpen(uri, ctypes.byref(handle))
        HandleObject.__init__(self, handle)
        self._devinfo = None
        if self.is_file():
            self.playback = PlaybackSupport(self)
        else:
            self.playback = None
        self._sensor_infos = {}

    def _close(self):
        oni.oniDeviceClose(self._handle)
        self.playback = None

    def get_device_info(self):
        if self._devinfo is None:
            self._devinfo = oni.OniDeviceInfo()
            oni.oniDeviceGetInfo(self._handle, ctypes.byref(self._devinfo))
        return self._devinfo
    device_info = property(get_device_info)

    def get_sensor_info(self, sensor_type):
        if sensor_type in self._sensor_infos:
            return self._sensor_infos[sensor_type]
        
        info = SensorInfo.from_device_handle(self._handle, sensor_type)
        self._sensor_infos[sensor_type] = info
        return info
    
    def has_sensor(self, sensor_type):
        return self.get_sensor_info(sensor_type) is not None

    def get_property(self, property_id, rettype):
        ret = rettype()
        oni.oniDeviceGetProperty(self._handle, property_id, ctypes.byref(ret), ctypes.sizeof(rettype))
        return ret
    def get_int_property(self, property_id):
        return self.get_property(property_id, ctypes.c_int).value
    def set_property(self, property_id, obj, size = None):
        obj, size = _py_to_ctype_obj(obj)
        if size is None:
            size = ctypes.sizeof(obj)
        oni.oniDeviceSetProperty(self._handle, property_id, ctypes.byref(obj), size)
    def is_property_supported(self, property_id):
        return bool(oni.oniDeviceIsPropertySupported(self._handle, property_id))

    def invoke(self, command_id, data, size = None):
        oni.oniDeviceInvoke(self._handle, command_id, data, size)
    def is_command_supported(self, command_id):
        return bool(oni.oniDeviceIsCommandSupported(self._handle, command_id))

    def is_image_registration_mode_supported(self, mode):
        return bool(oni.oniDeviceIsImageRegistrationModeSupported(self._handle, mode))
    def get_image_registration_mode(self):
        return self.get_property(oni.ONI_DEVICE_PROPERTY_IMAGE_REGISTRATION, oni.OniImageRegistrationMode)
    def set_image_registration_mode(self, mode):
        self.set_property(oni.ONI_DEVICE_PROPERTY_IMAGE_REGISTRATION, mode)

    def is_file(self):
        return (self.is_property_supported(oni.ONI_DEVICE_PROPERTY_PLAYBACK_SPEED) and
            self.is_property_supported(oni.ONI_DEVICE_PROPERTY_PLAYBACK_REPEAT_ENABLED) and
            self.is_property_supported(oni.ONI_DEVICE_COMMAND_SEEK))

    def set_depth_color_sync_enabled(self, enable):
        if enable:
            oni.oniDeviceEnableDepthColorSync(self._handle)
        else:
            oni.oniDeviceDisableDepthColorSync(self._handle)


@inherit_properties(oni.OniFrame, "_frame")
class VideoFrame(HandleObject):
    def __init__(self, pframe):
        self._frame = pframe[0]
        HandleObject.__init__(self, pframe)
    def _close(self):
        oni.oniFrameRelease(self._handle)
        self._frame = ClosedHandle
    
    def get_buffer(self):
        return (ctypes.c_uint8 * self.dataSize).from_address(self.data.value)

class CameraSettings(object):
    __slots__ = ["stream"]
    def __init__(self, stream):
        self.stream = weakref.proxy(stream)
    
    def get_auto_exposure(self):
        return bool(self.get_property(oni.ONI_STREAM_PROPERTY_AUTO_EXPOSURE, oni.OniBool))
    def set_auto_exposure(self, enabled):
        self.set_property(oni.ONI_STREAM_PROPERTY_AUTO_EXPOSURE, enabled)
    auto_exposure = property(get_auto_exposure, set_auto_exposure)

    def get_auto_white_balance(self):
        return bool(self.get_property(oni.ONI_STREAM_PROPERTY_AUTO_WHITE_BALANCE, oni.OniBool))
    def set_auto_white_balance(self, enabled):
        return self.set_property(oni.ONI_STREAM_PROPERTY_AUTO_WHITE_BALANCE, enabled)
    auto_white_balance = property(get_auto_white_balance, set_auto_white_balance)


class VideoStream(HandleObject):
    def __init__(self, device, sensor_type):
        self.device = device
        self.sensor_type = sensor_type
        self._callbacks = {}
        handle = oni.OniStreamHandle()
        oni.oniDeviceCreateStream(self.device._handle, sensor_type, ctypes.byref(self._handle))
        HandleObject.__init__(self, handle)
        if (self.is_property_supported(oni.ONI_STREAM_PROPERTY_AUTO_WHITE_BALANCE) and 
                self.is_property_supported(oni.ONI_STREAM_PROPERTY_AUTO_EXPOSURE)):
            self.camera = CameraSettings(self)
        else:
            self.camera = None
    
    def _close(self):
        oni.oniStreamDestroy(self._handle)
        self.camera = None
    
    def get_sensor_info(self):
        return SensorInfo.from_stream_handle(self._handle)
    
    def start(self):
        oni.oniStreamStart(self._handle)
    def stop(self):
        oni.oniStreamStop(self._handle)
    
    def readFrame(self):
        pframe = ctypes.POINTER(oni.OniFrame)()
        oni.oniStreamReadFrame(self._handle, ctypes.byref(pframe))
        return VideoFrame(pframe)
    
    def add_new_frame_listener(self, callback):
        """callback(stream : VideoStream) -> None"""
        cb_handle = oni.OniCallbackHandle()
        def callback_adapter(handle, cookie, callback = callback, self = self):
            callback(self)
        
        oni.oniStreamRegisterNewFrameCallback(self._handle, oni.OniNewFrameCallback(callback_adapter), 
            None, ctypes.byref(cb_handle))
        self._callbacks[cb_handle] = callback_adapter
        return cb_handle
    
    def remove_new_frame_listener(self, cb_handle):
        oni.oniStreamUnregisterNewFrameCallback(self._handle, cb_handle)
        self._callbacks.pop(cb_handle, None)

    def get_property(self, property_id, rettype):
        ret = rettype()
        oni.oniStreamGetProperty(self._handle, property_id, ctypes.byref(ret), ctypes.sizeof(rettype))
        return ret
    def get_int_property(self, property_id):
        return self.get_property(property_id, ctypes.c_int).value
    def set_property(self, property_id, obj, size = None):
        obj, size = _py_to_ctype_obj(obj)
        if size is None:
            size = ctypes.sizeof(obj)
        oni.oniStreamSetProperty(self._handle, property_id, ctypes.byref(obj), size)
    def is_property_supported(self, property_id):
        return bool(oni.oniStreamIsPropertySupported(self._handle, property_id))

    def invoke(self, command_id, data, size = None):
        data, size = _py_to_ctype_obj(data)
        if size is None:
            size = ctypes.sizeof(data)
        oni.oniStreamInvoke(self._handle, command_id, data, size)
    def is_command_supported(self, command_id):
        return bool(oni.oniStreamIsCommandSupported(self._handle, command_id))

    def get_video_mode(self):
        return self.get_property(oni.ONI_STREAM_PROPERTY_VIDEO_MODE, oni.OniVideoMode)
    def set_video_mode(self, video_mode):
        self.set_property(oni.ONI_STREAM_PROPERTY_VIDEO_MODE, video_mode)
    
    def get_max_pixel_value(self):
        return self.get_int_property(oni.ONI_STREAM_PROPERTY_MAX_VALUE)
    def get_min_pixel_value(self):
        return self.get_int_property(oni.ONI_STREAM_PROPERTY_MIN_VALUE)

    def is_cropping_supported(self):
        return self.is_property_supported(oni.ONI_STREAM_PROPERTY_CROPPING)
    def getCropping(self):
        return self.get_property(self.ONI_STREAM_PROPERTY_CROPPING, oni.OniCropping)
    def set_cropping(self, originX, originY, width, height):
        cropping = oni.OniCropping(enabled = True, originX = originX, originY = originY, width = width, height = height)
        self.set_property(oni.ONI_STREAM_PROPERTY_CROPPING, cropping)
    def resetCropping(self):
        self.set_property(oni.ONI_STREAM_PROPERTY_CROPPING, oni.OniCropping(enabled = False))

    def get_mirroring_enabled(self):
        return bool(self.get_property(self.ONI_STREAM_PROPERTY_MIRRORING, oni.OniBool))
    def setMirroringEnabled(self, enabled):
        self.set_property(oni.ONI_STREAM_PROPERTY_MIRRORING, enabled)
    
    def get_horizontal_fov(self):
        return self.get_property(oni.ONI_STREAM_PROPERTY_HORIZONTAL_FOV, ctypes.c_float).value
    def get_vertical_fov(self):
        return self.get_property(oni.ONI_STREAM_PROPERTY_VERTICAL_FOV, ctypes.c_float).value

    def get_number_of_frames(self):
        return self.get_int_property(oni.ONI_STREAM_PROPERTY_NUMBER_OF_FRAMES)


class Recorder(HandleObject):
    def __init__(self, filename):
        self.filename = filename
        handle = oni.OniRecorderHandle()
        oni.oniCreateRecorder(filename, ctypes.byref(handle))
        HandleObject.__init__(self, handle)
    def _close(self):
        oni.oniRecorderDestroy(ctypes.byref(self._handle))
    
    def attach(self, stream, allow_lossy_compression = False):
        oni.oniRecorderAttachStream(self._handle, stream._handle, allow_lossy_compression)
    def start(self):
        oni.oniRecorderStart(self._handle)
    def stop(self):
        oni.oniRecorderStop(self._handle)


def convert_world_to_depth(depthStream, worldX, worldY, worldZ):
    """const VideoStream& depthStream, float worldX, float worldY, float worldZ"""
    depthX = ctypes.c_float()
    depthY = ctypes.c_float()
    depthZ = ctypes.c_float()
    oni.oniCoordinateConverterWorldToDepth(depthStream._handle, worldX, worldY, worldZ, 
        ctypes.byref(depthX), ctypes.byref(depthY), ctypes.byref(depthZ))
    return depthX.value, depthY.value, depthZ.value 

def convert_depth_to_world(depthStream, depthX, depthY, depthZ):
    """const VideoStream& depthStream, float depthX, float depthY, float depthZ, float* pWorldX, float* pWorldY, float* pWorldZ"""
    depthX = ctypes.c_float()
    depthY = ctypes.c_float()
    depthZ = ctypes.c_float()
    oni.oniCoordinateConverterDepthToWorld(depthStream._handle, depthX, depthY, depthZ, 
        ctypes.byref(depthX), ctypes.byref(depthY), ctypes.byref(depthZ))
    return depthX.value, depthY.value, depthZ.value

def convert_depth_to_color(depthStream, colorStream, depthX, depthY, depthZ):
    """const VideoStream& depthStream, const VideoStream& colorStream, int depthX, int depthY, DepthPixel depthZ, int* pColorX, int* pColorY"""
    colorX = ctypes.c_int()
    colorY = ctypes.c_int()
    oni.oniCoordinateConverterDepthToColor(depthStream._handle, colorStream._handle, depthX, depthY, depthZ, 
        ctypes.byref(colorX), ctypes.byref(colorY));
    return colorX.value, colorY.value

class DeviceListener(object):
    _handle = None
    def _on_connected(self, pdevinfo, cookie):
        self.on_connected(pdevinfo[0])
    def _on_disconnected(self, pdevinfo, cookie):
        self.on_disconnected(pdevinfo[0])
    def _on_state_changed(self, pdevinfo, state, cookie):
        self.on_state_changed(pdevinfo[0], state)
    
    def on_connected(self, devinfo):
        pass
    def on_disconnected(self, devinfo):
        pass
    def on_state_changed(self, devinfo, state):
        pass
    
    def _register(self):
        if self._handle is not None:
            raise ValueError("This listener instance is already registered")
        self._handle = oni.OniCallbackHandle()
        self._callbacks = oni.OniDeviceCallbacks(
            deviceConnected = oni.OniDeviceInfoCallback(self._on_connected),
            deviceDisconnected = oni.OniDeviceInfoCallback(self._on_disconnected),
            deviceStateChanged = oni.OniDeviceStateCallback(self._on_state_changed),
        )
        oni.oniRegisterDeviceCallbacks(self._callbacks, None, ctypes.byref(self._handle))
    
    def _unregister(self):
        if self._handle is not None:
            oni.oniUnregisterDeviceCallbacks(self._handle)
            self._handle = None


def register_device_listener(listener):
    listener._register()
def unregister_device_listener(listener):
    listener._unregister()
    








