from crayola import CrayolaTestBase, SensorConfig


class TestResets(CrayolaTestBase):
    NUM_SOFT_RESETS = 500
    NUM_HARD_RESETS = 500
    HARD_RESET_DELAY = 6
    sensor_config = SensorConfig(depth = (320, 240, 30), ir = (640, 480, 30))
    read_correctness_frames = 120
    
    def test_soft_resets(self):
        for _ in range(self.NUM_SOFT_RESETS):
            self.device.configure(self.sensor_config)
            self.device.soft_reset()
            self.general_read_correctness(frames = self.read_correctness_frames)

    def test_hard_resets(self):
        for _ in range(self.NUM_HARD_RESETS):
            self.device.configure(self.sensor_config)
            self.device.hard_reset()
            self.general_read_correctness(frames = self.read_correctness_frames)





