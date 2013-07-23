import os
import time
from glob import glob
from primesense import openni2, _openni2 as c_api
from crayola.specs import specs_by_usb_name
from contextlib import contextmanager


class ExtendedDevice(openni2.Device):
    """
    This class extends the basic OpenNI Device class with extra non-public APIs, 
    used for testing
    """
    _depth_stream = None
    _ir_stream = None
    _color_stream = None
    
    @property
    def spec(self):
        """
        returns the device's spec (supported stream modes, etc)
        """
        return specs_by_usb_name[self.get_device_info().name]
    
    def soft_reset(self, sleep = 2):
        """
        performs a soft-reset of the device (also takes care of sleeping a little)
        """
        if self.get_device_info().name == "PS1080":
            self.set_property(c_api.XN_MODULE_PROPERTY_RESET, c_api.XnParamResetType.XN_RESET_TYPE_SOFT)
        else:
            self.invoke(c_api.PS_COMMAND_SOFT_RESET)
        time.sleep(sleep)
    
    def hard_reset(self, sleep = 6):
        """
        performs a hard-reset of the device (also takes care of sleeping a little and reopening 
        the device)
        """
        if self.get_device_info().name == "PS1080":
            self.set_property(c_api.XN_MODULE_PROPERTY_RESET, c_api.XnParamResetType.XN_RESET_TYPE_POWER)
        else:
            self.invoke(c_api.PS_COMMAND_POWER_RESET)
        time.sleep(sleep)
        self._reopen()
    
    def set_usb_bulk(self):
        """
        puts the device in USB bulk mode
        """
        if self.get_device_info().name == "PS1080":
            self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE,
                c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_BULK_ENDPOINTS)
        else:
            self.set_property(c_api.PS_PROPERTY_USB_INTERFACE,
                c_api.XnUsbInterfaceType.PS_USB_INTERFACE_BULK_ENDPOINTS)

    def set_usb_iso(self):
        """
        puts the device in USB ISO mode
        """
        if self.get_device_info().name == "PS1080":
            self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE, 
                c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_ISO_ENDPOINTS)
        else:
            self.set_property(c_api.PS_PROPERTY_USB_INTERFACE,
                c_api.XnUsbInterfaceType.PS_USB_INTERFACE_ISO_ENDPOINTS)

    @classmethod
    def _configure_stream(cls, stream, width, height, fps, pixfmt):
        if not stream:
            return None
        mode = openni2.VideoMode(fps = fps, resolutionX = width, resolutionY = height, pixelFormat = pixfmt)
        stream.set_video_mode(mode)
        stream.start()
        return stream

    def get_ir_stream(self, width, height, fps, pixfmt = openni2.PIXEL_FORMAT_GRAY16):
        """
        Creates an IR stream with the given configuration (closes the current one, if one exists)
        """
        if self._ir_stream:
            self._ir_stream.close()
        self._ir_stream = self.create_ir_stream()
        return self._configure_stream(self._ir_stream, width, height, fps, pixfmt)

    def get_depth_stream(self, width, height, fps, pixfmt = openni2.PIXEL_FORMAT_DEPTH_1_MM):
        """
        Creates a depth stream with the given configuration (closes the current one, if one exists)
        """
        if self._depth_stream:
            self._depth_stream.close()
        self._depth_stream = self.create_depth_stream()
        return self._configure_stream(self._depth_stream, width, height, fps, pixfmt)

    def get_color_stream(self, width, height, fps, pixfmt = openni2.PIXEL_FORMAT_RGB888):
        """
        Creates a color stream with the given configuration (closes the current one, if one exists)
        """
        if self._color_stream:
            self._color_stream.close()
        self._color_stream = self.create_color_stream()
        return self._configure_stream(self._color_stream, width, height, fps, pixfmt)

    def start_fwlog(self):
        """
        Start the FW log; returns the filename of the log file or None if it's not supported
        """
        try:
            self.invoke(openni2.c_api.PS_COMMAND_START_LOG)
        except openni2.OpenNIError:
            return None
        else:
            time.sleep(1)
            files = glob("./log/*.FirmwareLog.log")
            return os.path.abspath(max(files))
    
    def stop_fwlog(self):
        """
        Stop the FW log
        """
        try:
            self.invoke(openni2.c_api.PS_COMMAND_STOP_LOG)
        except openni2.OpenNIError:
            return None

    @contextmanager
    def fwlog(self):
        """
        FW log context manager. Usage::
        
            with dev.fwlog() as fn:
                s = dev.get_ir_stream()
                s.start()
        """
        fn = self.start_fwlog()
        try:
            yield fn
        finally:
            self.stop_fwlog()

    


