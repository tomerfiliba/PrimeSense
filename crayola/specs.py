from primesense import openni2


class DeviceSpec(object):
    usb_name = None
    
    color_modes = []
    ir_modes = []
    depth_modes = []


class PS1080Spec(DeviceSpec):
    usb_name = "PS1080"
    
    color_modes = [
        (320, 240, 30, openni2.PIXEL_FORMAT_RGB888),
        (320, 240, 30, openni2.PIXEL_FORMAT_YUV422),
        (320, 240, 30, openni2.PIXEL_FORMAT_YUYV),
        (320, 240, 15, openni2.PIXEL_FORMAT_RGB888),
        (320, 240, 15, openni2.PIXEL_FORMAT_YUV422),
        (320, 240, 15, openni2.PIXEL_FORMAT_YUYV),
        (320, 240, 60, openni2.PIXEL_FORMAT_RGB888),
        (320, 240, 60, openni2.PIXEL_FORMAT_YUV422),
        (320, 240, 60, openni2.PIXEL_FORMAT_YUYV),
        (640, 480, 30, openni2.PIXEL_FORMAT_RGB888),
        (640, 480, 30, openni2.PIXEL_FORMAT_YUV422),
        (640, 480, 30, openni2.PIXEL_FORMAT_YUYV),
        (640, 480, 15, openni2.PIXEL_FORMAT_RGB888),
        (640, 480, 15, openni2.PIXEL_FORMAT_YUV422),
        (640, 480, 15, openni2.PIXEL_FORMAT_YUYV),
        #(1280, 1024, 30, openni2.PIXEL_FORMAT_RGB888),
        #(1280, 1024, 30, openni2.PIXEL_FORMAT_GRAY8),
        #(1280, 1024, 30, openni2.PIXEL_FORMAT_YUV422),
        #(1280, 1024, 30, openni2.PIXEL_FORMAT_YUYV),
        #(1280, 720, 30, openni2.PIXEL_FORMAT_RGB888),
        #(1280, 720, 30, openni2.PIXEL_FORMAT_GRAY8),
        #(1280, 960, 30, openni2.PIXEL_FORMAT_RGB888),
        #(1280, 960, 30, openni2.PIXEL_FORMAT_GRAY8),
    ]
    
    ir_modes = [
        (320, 240, 30, openni2.PIXEL_FORMAT_GRAY16),
        (320, 240, 30, openni2.PIXEL_FORMAT_RGB888),
        (320, 240, 60, openni2.PIXEL_FORMAT_GRAY16),
        (320, 240, 60, openni2.PIXEL_FORMAT_RGB888),
        (640, 480, 30, openni2.PIXEL_FORMAT_GRAY16),
        (640, 480, 30, openni2.PIXEL_FORMAT_RGB888),
        #(1280, 1024, 30, openni2.PIXEL_FORMAT_GRAY16),
        #(1280, 1024, 30, openni2.PIXEL_FORMAT_RGB888),
    ]
    
    depth_modes = [
        (160, 120, 30, openni2.PIXEL_FORMAT_DEPTH_1_MM),
        (160, 120, 30, openni2.PIXEL_FORMAT_DEPTH_100_UM),
        (320, 240, 30, openni2.PIXEL_FORMAT_DEPTH_1_MM),
        (320, 240, 30, openni2.PIXEL_FORMAT_DEPTH_100_UM),
        (640, 480, 30, openni2.PIXEL_FORMAT_DEPTH_1_MM),
        (640, 480, 30, openni2.PIXEL_FORMAT_DEPTH_100_UM),
    ]


class PSLinkSpec(DeviceSpec):
    usb_name = "PSLink"
    
    color_modes = []
    
    ir_modes = [
        (640, 480, 30, openni2.PIXEL_FORMAT_GRAY16),
    ]
    
    depth_modes = [
        (160, 120, 30, openni2.PIXEL_FORMAT_DEPTH_1_MM),
        (320, 240, 30, openni2.PIXEL_FORMAT_DEPTH_1_MM),
        #(512, 384, 30, openni2.PIXEL_FORMAT_DEPTH_1_MM),
    ]


specs_by_usb_name = dict((cls.usb_name, cls) for cls in DeviceSpec.__subclasses__())




