from __future__ import print_function
from primelib import openni2


openni2.initialize()

d = openni2.Device.open_any()
print (d.get_device_info())

print ("IR", d.get_sensor_info(openni2.SENSOR_IR))
print ("DEPTH", d.get_sensor_info(openni2.SENSOR_DEPTH))
print ("COLOR", d.get_sensor_info(openni2.SENSOR_COLOR))

depth = d.create_depth_stream()
assert depth is not None

print ("v-fov:", depth.get_vertical_fov())
print ("h-fov:", depth.get_horizontal_fov())
print ("camera settings:", depth.camera)

depth.start()

for i in range(100):
    s = openni2.wait_for_any_stream([depth], 2)
    if not s:
        continue
    frame = depth.read_frame()
    
    if frame.videoMode.pixelFormat not in (openni2.PIXEL_FORMAT_DEPTH_100_UM, openni2.PIXEL_FORMAT_DEPTH_1_MM):
        print ("Unexpected frame format", frame.videoMode.pixelFormat)
        continue
    
    data = frame.get_buffer_as_uint16()
    middle_index = (frame.height + 1) * frame.width // 2
    print ("ts = %s, middle = 0x%02x" % (frame.timestamp, data[middle_index]))

print ("\ngoodbye")
depth.stop()
openni2.unload()


