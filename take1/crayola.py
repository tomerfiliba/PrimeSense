import logging
from primelib import openni2, _openni2 as c_api
import time


logger = logging.getLogger("crayola")

class ExtendedDevice(openni2.Device):
    def soft_reset(self):
        self.set_property(c_api.XN_MODULE_PROPERTY_RESET, c_api.XnParamResetType.XN_RESET_TYPE_SOFT)
        #self._reopen()
        
    def hard_reset(self):
        self.set_property(c_api.XN_MODULE_PROPERTY_RESET, c_api.XnParamResetType.XN_RESET_TYPE_POWER)
        time.sleep(6)
        self._reopen()
    
    def set_usb_bulk(self):
        self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE, 
            c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_BULK_ENDPOINTS)

    def set_usb_iso(self):
        self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE, 
            c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_ISO_ENDPOINTS)


class CrayolaTestBase(object):
    _the_device = None
    _ir_stream = None
    _depth_stream = None
    _color_stream = None
    
    @classmethod
    def _get_device(cls):
        if cls._the_device is None:
            openni2.initialize()
            openni2.configure_logging("./logs", 1)
            cls._the_device = ExtendedDevice.open_any()
        else:
            cls._the_device._reopen()
        for name in ["_ir_stream", "_depth_stream", "_color_stream"]:
            stream = getattr(cls, name)
            if stream:
                stream.close()
                setattr(cls, name, None)
        
        return cls._the_device

    @classmethod
    def setUpClass(cls):
        cls.logger = logger
    
    def setUp(self):
        self.device = self._get_device()
    
    def general_read_correctness(self, seconds, error_threshold = 0.05):
        modes = [(320, 240, 30), (640, 480, 30)]
        stream_factories = [self.get_ir_stream, self.get_color_stream, self.get_depth_stream]
        
        def callback(stream):
            with stream.read_frame():
                frames[0] += 1
        
        for w, h, fps in modes:
            for streamfac in stream_factories:
                stream = streamfac(w, h, fps)
                if not stream:
                    continue
                
                with stream:
                    self.logger.info("testing %s at %sx%s, %s fps", streamfac.__name__, w, h, fps)
                    
                    frames = [0]
                    stream.register_new_frame_listener(callback)
                    time.sleep(seconds)
                    stream.unregister_new_frame_listener(callback)
                    
                    expected = seconds * fps
                    min_expected = expected * (1 - error_threshold)
                    max_expected = expected * (1 + error_threshold)
                    self.logger.info("got %s, expected %s..%s", frames[0], min_expected, max_expected)
                    assert min_expected <= frames[0] <= max_expected

    @classmethod
    def _configure_stream(cls, stream, width, height, fps, format):
        if not stream:
            return None
        mode = c_api.OniVideoMode(fps = fps, resolutionX = width, resolutionY = height, pixelFormat = format)
        stream.set_video_mode(mode)
        stream.start()
        return stream

    @classmethod
    def get_ir_stream(cls, width, height, fps, format = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_GRAY16):
        if cls._ir_stream:
            cls._ir_stream.close()
        cls._ir_stream = cls._the_device.create_ir_stream()
        return cls._configure_stream(cls._ir_stream, width, height, fps, format)

    @classmethod
    def get_depth_stream(cls, width, height, fps, format = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM):
        if cls._ir_stream:
            cls._ir_stream.close()
            cls._ir_stream = None
        if cls._depth_stream:
            cls._depth_stream.close()
        cls._depth_stream = cls._the_device.create_depth_stream()
        return cls._configure_stream(cls._depth_stream, width, height, fps, format)

    @classmethod
    def get_color_stream(cls, width, height, fps, format = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_RGB888):
        if cls._ir_stream:
            cls._ir_stream.close()
            cls._ir_stream = None
        if cls._color_stream:
            cls._color_stream.close()
        cls._color_stream = cls._the_device.create_color_stream()
        return cls._configure_stream(cls._color_stream, width, height, fps, format)











