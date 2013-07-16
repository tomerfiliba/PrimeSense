import time
import logging
from primelib import openni2, _openni2 as c_api
from nose.plugins.skip import SkipTest
import sys


logger = logging.getLogger("crayola")

class ExtendedDevice(openni2.Device):
    """
    This class extends the basic OpenNI Device class with extra non-public APIs, 
    used for testing purposes
    """
    
    def soft_reset(self):
        """
        performs a soft-reset of the device
        """
        self.set_property(c_api.XN_MODULE_PROPERTY_RESET, c_api.XnParamResetType.XN_RESET_TYPE_SOFT)
        #self._reopen()
        
    def hard_reset(self, sleep = 6):
        """
        performs a hard-reset of the device (also takes care of sleeping a little and reopening 
        the device)
        """
        self.set_property(c_api.XN_MODULE_PROPERTY_RESET, c_api.XnParamResetType.XN_RESET_TYPE_POWER)
        time.sleep(sleep)
        self._reopen()
    
    def set_usb_bulk(self):
        """
        puts the device in USB bulk mode
        """
        self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE, 
            c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_BULK_ENDPOINTS)

    def set_usb_iso(self):
        """
        puts the device in USB ISO mode
        """
        self.set_property(c_api.XN_MODULE_PROPERTY_USB_INTERFACE, 
            c_api.XnSensorUsbInterface.XN_SENSOR_USB_INTERFACE_ISO_ENDPOINTS)


class CrayolaTestBase(object):
    """
    The base class for crayola tests. Your tests *must* derive from this class, 
    or bad things will ensue.
    
    Between each 
    
    """
    
    THRESHOLD = 0.10
    _the_device = None
    _ir_stream = None
    _depth_stream = None
    _color_stream = None
    
    @classmethod
    def _get_device(cls):
        openni2.unload()
        openni2.initialize()
        openni2.configure_logging(severity = 1)
        if cls._the_device:
            cls._the_device.close()
        try:
            cls._the_device = ExtendedDevice.open_any()
        except openni2.OpenNIError as ex:
            if "no devices found" in str(ex):
                raise SkipTest("No device found")
            else:
                raise
        
        for name in ["_ir_stream", "_depth_stream", "_color_stream"]:
            stream = getattr(cls, name)
            if stream:
                stream.close()
                setattr(cls, name, None)
        
        cls.oni_logfile = openni2.get_log_filename()
        return cls._the_device

    @classmethod
    def setUpClass(cls):
        cls.logger = logger
    
    def setUp(self):
        self.device = self._get_device()
    
    def tearDown(self):
        if sys.exc_info()[0] is not None:
            oni_logfile = getattr(self, "oni_logfile", None)
            if oni_logfile:
                sys.__stderr__.write("ONI LOG %s\n" % (oni_logfile,))
    
    def general_read_correctness(self, seconds, error_threshold = THRESHOLD):
        modes = [(320, 240, 30), (640, 480, 30)]
        stream_factories = [self.get_ir_stream, self.get_color_stream, self.get_depth_stream]
        
        for w, h, fps in modes:
            for streamfac in stream_factories:
                try:
                    stream = streamfac(w, h, fps)
                except openni2.OpenNIError as ex:
                    self.logger.warning("Can't configure %s at %sx%s, %s fps: %s", streamfac.__name__, w, h, fps, ex)
                    continue
                if not stream:
                    self.logger.warning("Can't configure %s at %sx%s, %s fps: %s", streamfac.__name__, w, h, fps, ex)
                    continue
                
                with stream:
                    self.verify_stream_fps(stream, seconds, error_threshold)

    def verify_stream_fps(self, stream, seconds, error_threshold = THRESHOLD):
        """
        Verifies the number of frames read from the given stream 
        """
        mode = stream.get_video_mode()
        timestamps = []
        empty_frames = [0]
        
        def callback(stream):
            with stream.read_frame() as frm:
                timestamps.append(frm.timestamp)
                if len(timestamps) % 2 == 0:
                    if not any(frm.get_buffer_as_uint8()):
                        empty_frames[0] += 1

        stream.register_new_frame_listener(callback)
        time.sleep(seconds)
        stream.unregister_new_frame_listener(callback)
        
        expected = mode.fps * seconds
        min_expected = expected * (1 - error_threshold)
        max_expected = expected * (1 + error_threshold)
        frames = len(timestamps)
        empty_frames = empty_frames[0]
        self.logger.info("got %s frames (expected %s..%s), %d empty", frames, min_expected, max_expected, empty_frames)
        
        assert min_expected <= frames <= max_expected, "Too few/many frames"
        assert empty_frames <= frames * error_threshold, "Too many empty frames"
        assert timestamps == sorted(timestamps), "Timestamps are not monotonically increasing"

    @classmethod
    def _configure_stream(cls, stream, width, height, fps, pixfmt):
        if not stream:
            return None
        mode = c_api.OniVideoMode(fps = fps, resolutionX = width, resolutionY = height, pixelFormat = pixfmt)
        stream.set_video_mode(mode)
        stream.start()
        return stream

    @classmethod
    def get_ir_stream(cls, width, height, fps, pixfmt = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_GRAY16):
        """
        Creates an IR stream with the given configuration.
        """
        if cls._ir_stream:
            cls._ir_stream.close()
        cls._ir_stream = cls._the_device.create_ir_stream()
        return cls._configure_stream(cls._ir_stream, width, height, fps, pixfmt)

    @classmethod
    def get_depth_stream(cls, width, height, fps, pixfmt = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM):
        """
        Creates a depth stream with the given configuration.
        
        .. note:: Cannot be used in conjunction with an open IR stream. If an IR stream is open, it will be 
        closed first
        """
        if cls._ir_stream:
            cls._ir_stream.close()
            cls._ir_stream = None
        if cls._depth_stream:
            cls._depth_stream.close()
        cls._depth_stream = cls._the_device.create_depth_stream()
        return cls._configure_stream(cls._depth_stream, width, height, fps, pixfmt)

    @classmethod
    def get_color_stream(cls, width, height, fps, pixfmt = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_RGB888):
        """
        Creates a color stream with the given configuration.
        
        .. note:: Cannot be used in conjunction with an open IR stream. If an IR stream is open, it will be 
        closed first
        """
        if cls._ir_stream:
            cls._ir_stream.close()
            cls._ir_stream = None
        if cls._color_stream:
            cls._color_stream.close()
        cls._color_stream = cls._the_device.create_color_stream()
        return cls._configure_stream(cls._color_stream, width, height, fps, pixfmt)











