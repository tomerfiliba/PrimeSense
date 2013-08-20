import time
import logging
from primesense import openni2
from nose.plugins.skip import SkipTest
from crayola.ext_device import ExtendedDevice


logger = logging.getLogger("crayola")


class CrayolaTestBase(object):
    """
    The base class for crayola tests. Your tests *must* derive from this class, 
    or bad things will ensue.
    
    Note that ``setUp`` is called between each test to reset openni and open all available devices.
    You can use them as ``self.device`` (the first device) or ``self.devices`` (list of all connected 
    devices). 
    """
    
    ERROR_THRESHOLD = 0.10
    _all_devices = ()
    logger = logger
    PREREQUISITES = []
    
    def setUp(self):
        """
        Called before each test case. It will skip the test if not devices are connected
        or if any of the predicates in ``self.PREREQUISITES`` returns ``False``
        """
        self.report_error_links = []
        openni2.initialize()
        openni2.configure_logging("./log", severity = 0)
        self.add_log_link("OpenNI log", openni2.get_log_filename())
        
        self._all_devices = ExtendedDevice.open_all()
        if not self._all_devices:
            logger.error("No devices found")
            raise SkipTest("No devices found")
        
        for prereq in self.PREREQUISITES:
            if not prereq(self):
                logger.error("prerequisite %s failed", prereq)
                raise SkipTest("Prerequisites failed: %s" % (prereq,))
    
    def tearDown(self):
        """
        called after each test case
        """
        for dev in self._all_devices:
            dev.close()
        openni2.unload()
    
    def add_log_link(self, name, filepath):
        """
        Adds a link (URL/file path) to the log. There are collected by Crayola Report
        """
        self.report_error_links.append((name, filepath))
    
    @property
    def device(self):
        """
        The first device
        """
        return self._all_devices[0]
    
    @property
    def devices(self):
        """
        A list of all connected devices
        """
        return self._all_devices
    
    def general_read_correctness(self, seconds, error_threshold = ERROR_THRESHOLD):
        """
        Runs each ``verify_stream_fps`` on every stream mode that's supported by any of 
        the connected devices. For ``seconds`` and ``error_threshold`` -- see the docs of
        ``verify_stream_fps``
        """
        for dev in self.devices:
            self.general_read_correctness_for_device(dev, seconds, error_threshold)

    def general_read_correctness_for_device(self, device, seconds, error_threshold = ERROR_THRESHOLD):
        """
        Like general_read_correctness, but for a specific device
        """
        factories = [
            ("color", device.get_color_stream, device.spec.color_modes),
            ("IR", device.get_ir_stream, device.spec.ir_modes),
            ("depth", device.get_depth_stream, device.spec.depth_modes),
        ]
        for name, factory, modes in factories:
            for w, h, fps, fmt in modes:
                try:
                    stream = factory(w, h, fps, fmt)
                except openni2.OpenNIError as ex:
                    logger.warning("Can't configure %s at %sx%s, %s fps: %s", name, w, h, fps, ex)
                    continue
                if not stream:
                    logger.warning("Can't configure %s at %sx%s, %s fps: %s", name, w, h, fps, ex)
                    continue
                with stream:
                    self.verify_stream_fps(stream, seconds, error_threshold)

    @classmethod
    def verify_stream_fps(cls, stream, seconds, error_threshold = ERROR_THRESHOLD):
        """
        Verifies the number of frames read from the given stream.
        
        :param stream: the stream to test
        :param seconds: the number of seconds (float) to wait; this controls how many frames
                        are expected (expected frames = seconds * fps) 
        :param error_threshold: the error threshold (a float in range 0..1). controls
                        the allowed error-rate
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
        
        expected_fps = mode.fps
        
        if stream.get_sensor_info().sensorType == openni2.SENSOR_IR and mode.resolutionX == 1280:
            expected_fps = 9
        elif stream.get_sensor_info().sensorType == openni2.SENSOR_COLOR and mode.resolutionX == 1280:
            if mode.resolutionY == 1024:
                expected_fps = 7
            elif mode.resolutionY == 960:
                expected_fps = 14
        
        expected = expected_fps * seconds
        print expected
        min_expected = expected * (1 - error_threshold)
        max_expected = expected * (1 + error_threshold)
        frames = len(timestamps)
        empty_frames = empty_frames[0]
        logger.info("%sx%s@%s/%s: got %s frames (allowed %s..%s), %d empty", mode.resolutionX, mode.resolutionY,
            mode.fps, str(mode.pixelFormat).rsplit("_", 1)[-1], frames, min_expected, max_expected, empty_frames)
        
        assert frames >= min_expected, "Too few frames"
        assert frames <= max_expected, "Too many frames"
        assert empty_frames <= frames * error_threshold, "Too many empty frames"
        assert timestamps == sorted(timestamps), "Timestamps are not monotonically increasing"



