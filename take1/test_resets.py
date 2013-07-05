from crayola import CrayolaTestBase
import time


class TestResets(CrayolaTestBase):
    NUM_SOFT_RESETS = 5
    NUM_HARD_RESETS = 5
    HARD_RESET_DELAY = 6
    
    def test_soft_resets(self):
        for i in range(self.NUM_SOFT_RESETS):
            self.logger.info("attempt %d", i)
            self.device.set_usb_iso()
            self.device.soft_reset()
            
            #self.general_read_correctness(frames = self.read_correctness_frames)

    def test_hard_resets(self):
        for i in range(self.NUM_HARD_RESETS):
            self.logger.info("attempt %d", i)
            self.device.set_usb_iso()
            self.device.hard_reset()
            
            #self.general_read_correctness(frames = self.read_correctness_frames)




