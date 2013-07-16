from crayola import CrayolaTestBase


class TestResets(CrayolaTestBase):
    NUM_SOFT_RESETS = 4
    NUM_HARD_RESETS = 2
    
    def test_soft_resets(self):
        for _ in range(self.NUM_SOFT_RESETS):
            self.device.set_usb_iso()
            self.device.soft_reset()
            self.general_read_correctness(3, error_threshold = 0.90)

    def test_hard_resets(self):
        for _ in range(self.NUM_HARD_RESETS):
            self.device.set_usb_iso()
            self.device.hard_reset()
            self.general_read_correctness(3)





