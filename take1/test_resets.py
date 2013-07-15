from crayola import CrayolaTestBase
from primelib.openni2 import c_api, OpenNIError


class TestResets(CrayolaTestBase):
    NUM_SOFT_RESETS = 4
    NUM_HARD_RESETS = 2
    
    def test_soft_resets(self):
        for _ in range(self.NUM_SOFT_RESETS):
            self.device.set_usb_iso()
            self.device.soft_reset()
            self.general_read_correctness(3, error_threshold = 0.50)

    def test_hard_resets(self):
        for _ in range(self.NUM_HARD_RESETS):
            self.device.set_usb_iso()
            self.device.hard_reset()
            self.general_read_correctness(3)


class TestPermutations(CrayolaTestBase):
    def _test_permutations(self, stream_factory, modes, formats, error_threshold = CrayolaTestBase.THRESHOLD):
        for fmt in formats:
            for w, h, fps in modes:
                try:
                    stream = stream_factory(w, h, fps, fmt)
                except OpenNIError as ex:
                    self.logger.warning("Can't configure %s at %sx%s, fps=%s, fmt=%s: %s", 
                        stream_factory.__name__, w, h, fps, fmt, ex)
                    continue
                if not stream:
                    self.logger.warning("Can't configure %s at %sx%s, fps=%s, fmt=%s: %s", 
                        stream_factory.__name__, w, h, fps, fmt, ex)
                    continue
                with stream:
                    self.verify_stream_fps(stream, 3, error_threshold)
    
    def test_permutations_color(self):
        modes = [(320, 240, 30), (320, 240, 60), (640, 480, 30)]
        formats = [
            c_api.OniPixelFormat.ONI_PIXEL_FORMAT_RGB888,
            c_api.OniPixelFormat.ONI_PIXEL_FORMAT_YUV422,
            c_api.OniPixelFormat.ONI_PIXEL_FORMAT_JPEG,
            c_api.OniPixelFormat.ONI_PIXEL_FORMAT_YUYV,
        ]
        self.device.set_usb_iso()
        self._test_permutations(self.get_color_stream, modes, formats)

    def test_permutations_depth(self):
        modes = [(320, 240, 30), (320, 240, 60), (640, 480, 30)]
        formats = [
            c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM,
            c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_100_UM,
        ]
        self.device.set_usb_iso()
        self._test_permutations(self.get_depth_stream, modes, formats)

    def test_permutations_ir(self):
        modes = [(320, 240, 30), (320, 240, 60), (640, 480, 30)]
        formats = [
            c_api.OniPixelFormat.ONI_PIXEL_FORMAT_GRAY16,
        ]
        self.device.set_usb_iso()
        self._test_permutations(self.get_ir_stream, modes, formats)









