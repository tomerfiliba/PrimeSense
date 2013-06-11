from primelib import openni2
import os
import time


openni2.initialize()

assert openni2.Device.enumerate_uris()
dev = openni2.Device.open_any()
assert dev.get_device_info()
assert dev.get_sensor_info(openni2.SENSOR_IR)
assert dev.get_sensor_info(openni2.SENSOR_DEPTH)
assert dev.get_sensor_info(openni2.SENSOR_COLOR)

dev.is_image_registration_mode_supported(openni2.IMAGE_REGISTRATION_OFF)
dev.is_image_registration_mode_supported(openni2.IMAGE_REGISTRATION_DEPTH_TO_COLOR)

depth_stream = dev.create_depth_stream()
color_stream = dev.create_color_stream()
ir_stream = dev.create_ir_stream()
assert depth_stream
assert color_stream
assert ir_stream

dev.is_file()
dev.is_command_supported(openni2.c_api.ONI_DEVICE_COMMAND_SEEK)
dev.get_depth_color_sync_enabled()
dev.set_depth_color_sync_enabled(True)
dev.get_depth_color_sync_enabled()
mode = dev.get_image_registration_mode()
dev.set_image_registration_mode(mode)

# VideoStream ########################
assert color_stream.camera
assert color_stream.get_sensor_info()

depth_stream.start()
color_stream.start()
#ir_stream.start()

# for some reason, it may fail on mac and linux (with a timeout) if we call it too soon
time.sleep(10)

for i in range(5):
    s = openni2.wait_for_any_stream([depth_stream], 10)
    if s:
        break
assert s
frm = depth_stream.read_frame()
assert frm
buf1 = frm.get_buffer_as_uint8()
buf2 = frm.get_buffer_as_uint16()
assert (buf1[0] + buf1[1] << 8) == buf2[0]

s = openni2.wait_for_any_stream([color_stream], 10)
assert s
frm = color_stream.read_frame()
assert frm

vm = color_stream.get_video_mode()
color_stream.set_video_mode(vm)

depth_stream.get_max_pixel_value()
depth_stream.get_min_pixel_value()
color_stream.is_cropping_supported()
color_stream.get_cropping()
color_stream.set_cropping(0, 0, 200, 200)
color_stream.reset_cropping()

color_stream.get_mirroring_enabled()
color_stream.set_mirroring_enabled(True)
color_stream.get_horizontal_fov()
color_stream.get_vertical_fov()
#color_stream.get_number_of_frames()

## CameraSettings ###########################################
color_stream.camera.get_auto_exposure()
color_stream.camera.set_auto_exposure(True)
color_stream.camera.get_auto_white_balance()
color_stream.camera.set_auto_white_balance(True)
color_stream.camera.get_gain()
color_stream.camera.set_gain(100)
color_stream.camera.get_exposure()
color_stream.camera.set_exposure(True)

## Recorder ###################################
rec = depth_stream.get_recoder("tmp.dat")
rec.start()
time.sleep(1)
rec.stop()
assert os.stat("tmp.dat").st_size
os.remove("tmp.dat")

## Top-level ############################
openni2.convert_world_to_depth(depth_stream, 30, 40, 50)
openni2.convert_depth_to_world(depth_stream, 30, 40, 50)
openni2.convert_depth_to_color(depth_stream, color_stream, 30, 40, 50)

## Callbacks ############################

cb_called = False
def cb(stream):
    global cb_called
    cb_called = True

print "registering frame listener (wait 3 sec)"
depth_stream.register_new_frame_listener(cb)
time.sleep(3)
print "unregistering frame listener (wait 3 sec)"
depth_stream.unregister_new_frame_listener(cb)
assert cb_called
cb_called = False
time.sleep(3)
assert not cb_called


class MyListener(openni2.DeviceListener):
    was_connected = False
    was_disconnected = False
    
    def on_connected(self, devinfo):
        print "on_connected", devinfo
        self.was_connected = True
    def on_disconnected(self, devinfo):
        print "on_disconnected", devinfo
        self.was_disconnected = True
    def on_state_changed(self, devinfo, state):
        print "on_state_changed", devinfo, state

listener = MyListener()
openni2.register_device_listener(listener)
print "Remove/add devices (30 sec)"
time.sleep(30)
openni2.unregister_device_listener(listener)

#assert listener.was_disconnected
#assert listener.was_connected


ir_stream.stop()
color_stream.stop()
depth_stream.stop()
openni2.unload()
print "all done"

