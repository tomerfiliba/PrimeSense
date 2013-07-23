from crayola import CrayolaTestBase
from primesense import openni2


class TestPermutations(CrayolaTestBase):
    def _test_permutations(self, stream_factory, modes, error_threshold = CrayolaTestBase.ERROR_THRESHOLD):
        for w, h, fps, fmt in modes:
            try:
                stream = stream_factory(w, h, fps, fmt)
            except openni2.OpenNIError as ex:
                self.logger.warn("Can't open %s at %sx%s/%s (%s): %s", stream_factory, w, h, fps, fmt, ex)
                continue
            if not stream:
                self.logger.warn("Can't open %s at %sx%s/%s (%s)", stream_factory, w, h, fps, fmt)
                continue
            
            with stream:
                self.verify_stream_fps(stream, 2, error_threshold)
    
    def test_permutations_color(self):
        for dev in self.devices:
            dev.set_usb_iso()
            self._test_permutations(dev.get_color_stream, dev.spec.color_modes)

    def test_permutations_depth(self):
        for dev in self.devices:
            dev.set_usb_iso()
            self._test_permutations(dev.get_depth_stream, dev.spec.depth_modes)

    def test_permutations_ir(self):
        for dev in self.devices:
            dev.set_usb_iso()
            self._test_permutations(dev.get_ir_stream, dev.spec.ir_modes)





