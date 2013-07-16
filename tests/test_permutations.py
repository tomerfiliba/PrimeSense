from crayola import CrayolaTestBase
from primesense import openni2


class TestPermutations(CrayolaTestBase):
    def _test_permutations(self, stream_factory, modes, formats, error_threshold = CrayolaTestBase.ERROR_THRESHOLD):
        for fmt in formats:
            for w, h, fps in modes:
                try:
                    stream = stream_factory(w, h, fps, fmt)
                except openni2.OpenNIError as ex:
                    self.logger.warning("Can't configure %s at %sx%s, fps=%s, fmt=%s: %s", 
                        stream_factory.__name__, w, h, fps, fmt, ex)
                    continue
                if not stream:
                    self.logger.warning("Can't configure %s at %sx%s, fps=%s, fmt=%s: %s", 
                        stream_factory.__name__, w, h, fps, fmt, ex)
                    continue
                with stream:
                    self.verify_stream_fps(stream, 3, error_threshold)
    
    def _test_permutations_color(self):
        modes = [(320, 240, 30), (320, 240, 60), (640, 480, 30)]
        formats = [
            openni2.PIXEL_FORMAT_RGB888,
            openni2.PIXEL_FORMAT_YUV422,
            openni2.PIXEL_FORMAT_JPEG,
            openni2.PIXEL_FORMAT_YUYV,
        ]
        self.device.set_usb_iso()
        self._test_permutations(self.get_color_stream, modes, formats)

    def _test_permutations_depth(self):
        modes = [(320, 240, 30), (320, 240, 60), (640, 480, 30)]
        formats = [
            openni2.PIXEL_FORMAT_DEPTH_1_MM,
            openni2.PIXEL_FORMAT_DEPTH_100_UM,
        ]
        self.device.set_usb_iso()
        self._test_permutations(self.get_depth_stream, modes, formats)

    def test_permutations_ir(self):
        modes = [(320, 240, 30), (320, 240, 60), (640, 480, 30)]
        formats = [
            openni2.PIXEL_FORMAT_GRAY16,
        ]
        self.device.set_usb_iso()
        self._test_permutations(self.get_ir_stream, modes, formats)





