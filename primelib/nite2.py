import os
import ctypes
from primelib import _nite2, openni2
from primelib.utils import inherit_properties, ClosedHandle, HandleObject, InitializationError


_default_dll_directories = [".", "c:\\program files\\prime sense\\nite2\\redist", 
    "c:\\program files (x86)\\prime sense\\nite2\\redist"]

_nite2_initialized = False
def initialize(dll_directories = _default_dll_directories):
    global _nite2_initialized
    if _nite2_initialized:
        raise InitializationError("NiTE2 already initialized")
    if isinstance(dll_directories, str):
        dll_directories = [dll_directories]
    
    found = False
    prev = os.getcwd()
    exceptions = []
    
    for dlldir in dll_directories:
        if not os.path.isdir(dlldir):
            exceptions.append((dlldir, "Directory does not exist"))
            continue
        try:
            os.chdir(dlldir)
            _nite2.load_dll("NiTE2")
            _nite2.niteInitialize()
        except Exception as ex:
            exceptions.append((dlldir, ex))
        else:
            found = True
            break
    os.chdir(prev)
    if not found:
        raise InitializationError("NiTE2 could not be loaded:\n    %s" % 
            ("\n    ".join("%s: %s" % (dir, ex) for dir, ex in exceptions)),)

    _nite2_initialized = True

def is_initialized():
    return _nite2_initialized

def unload():
    global _nite2_initialized
    _nite2.niteShutdown()
    _nite2_initialized = False

def get_version():
    return _nite2.niteGetVersion()

Point3f = _nite2.NitePoint3f
Plane = _nite2.NitePlane
Quaternion = _nite2.NiteQuaternion
BoundingBox = _nite2.NiteBoundingBox
UserId = _nite2.NiteUserId
HandId = _nite2.NiteHandId
UserMap = _nite2.NiteUserMap
SkeletonJoint = _nite2.NiteSkeletonJoint

@inherit_properties(_nite2.NitePoseData, "_posedata")
class PoseData(object):
    __slots__ = ["_posedata"]
    def __init__(self, posedata):
        self._posedata = posedata
    def is_held(self):
        return (self.state & _nite2.NitePoseState.NITE_POSE_STATE_IN_POSE) != 0
    def is_entered(self):
        return (self.state & _nite2.NitePoseState.NITE_POSE_STATE_ENTER) != 0
    def is_exited(self):
        return (self.state & _nite2.NitePoseState.NITE_POSE_STATE_EXIT) != 0

@inherit_properties(_nite2.NiteSkeleton, "_skeleton")
class Skeleton(object):
    __slots__ = ["_skeleton"]
    def __init__(self, skeleton):
        self._skeleton = skeleton
    def get_joint(self, joint_type):
        return self.joints[type]

@inherit_properties(_nite2.NiteUserData, "_userdata")
class UserData(object):
    __slots__ = ["_userdata"]
    def __init__(self, userdata):
        self._userdata = userdata
    def is_new(self):
        return (self.state & _nite2.NiteUserState.NITE_USER_STATE_NEW) != 0
    def is_visible(self):
        return (self.state & _nite2.NiteUserState.NITE_USER_STATE_VISIBLE) != 0;
    def is_lost(self):
        return (self.state & _nite2.NiteUserState.NITE_USER_STATE_LOST) != 0;
    def get_pose(self, posetype):
        return PoseData(self.poses[posetype])

@inherit_properties(_nite2.NiteUserTrackerFrame, "_frame")
class UserTrackerFrame(HandleObject):
    __slots__ = ["_frame", "_user_tracker_handle", "_depth_frame", "users", "users_by_id"]
    def __init__(self, pframe, user_tracker_handle):
        self._frame = pframe[0]
        self._user_tracker_handle = user_tracker_handle
        self._depth_frame = None
        HandleObject.__init__(self, pframe)
        self.users = []
        self.users_by_id = {}
        for i in range(self.pUser):
            u = UserData(self.pUser[i])
            self.users.append(u)
            self.users_by_id[u.id] = u
    
    def _close(self):
        _nite2.niteUserTrackerFrameRelease(self._user_tracker_handle, self._handle)
        self._frame = ClosedHandle
        self._user_tracker_handle = ClosedHandle
        del self.users[:]
    
    def get_depth_frame(self):
        if self._depth_frame is None:
            self._depth_frame = openni2.VideoFrame(self.pDepthFrame)
        return self._depth_frame

class UserTracker(HandleObject):
    def __init__(self, device):
        handle = _nite2.NiteUserTrackerHandle()
        if not device:
            _nite2.niteInitializeUserTracker(ctypes.byref(handle))
        else:
            _nite2.niteInitializeUserTrackerByDevice(device._handle, ctypes.byref(handle))
        HandleObject.__init__(self, handle)

    def _close(self):
        _nite2.niteShutdownUserTracker(self._handle)

    def read_frame(self):
        pnf = ctypes.POINTER(_nite2.NiteUserTrackerFrame)()
        _nite2.niteReadUserTrackerFrame(self._handle, ctypes.byref(pnf))
        return UserTrackerFrame(pnf, self._handle)

    def set_skeleton_smoothing_factor(self, factor):
        return _nite2.niteSetSkeletonSmoothing(self._handle, factor)
    def get_skeleton_smoothing_factor(self):
        factor = ctypes.c_float()
        _nite2.niteGetSkeletonSmoothing(self._handle, ctypes.byref(factor))
        return factor.value
    skeleton_smoothing_factor = property(get_skeleton_smoothing_factor, set_skeleton_smoothing_factor)

    def start_skeleton_tracking(self, userid):
        _nite2.niteStartSkeletonTracking(self._handle, userid)
    def stop_skeleton_tracking(self, userid):
        _nite2.niteStopSkeletonTracking(self._handle, userid)

    def start_pose_detection(self, userid, posetype):
        _nite2.niteStartPoseDetection(self._handle, userid, posetype)
    def stop_pose_detection(self, userid, posetype):
        _nite2.niteStopPoseDetection(self._handle, userid, posetype)

    def add_listener(self, listener):
        listener._register(self)
    def remove_listener(self, listener):
        listener._unregister()

    def convert_joint_coordinates_to_depth(self,  x, y, z):
        outX = ctypes.c_float()
        outY = ctypes.c_float()
        _nite2.niteConvertJointCoordinatesToDepth(self._handle, x, y, z, ctypes.byref(outX), ctypes.byref(outY))
        return (outX.value, outY.value)
    
    def convert_depth_coordinates_to_joint(self, x, y, z):
        outX = ctypes.c_float()
        outY = ctypes.c_float()
        _nite2.niteConvertDepthCoordinatesToJoint(self._handle, x, y, z, ctypes.byref(outX), ctypes.byref(outY))
        return (outX.value, outY.value)

class UserTrackerListener(object):
    def __init__(self):
        self._callbacks = _nite2.NiteUserTrackerCallbacks(readyForNextFrame = self._on_ready_for_next_frame)
        self._pcallbacks = ctypes.pointer(self._callbacks)
        self.user_tracker = None
    
    def _register(self, user_tracker):
        if self.user_tracker is not None:
            raise ValueError("Listener already registered")
        self.user_tracker = user_tracker
        _nite2.niteRegisterUserTrackerCallbacks(self.user_tracker._handle, self._pcallbacks, None)
    def _unregister(self):
        if self.user_tracker is None:
            raise ValueError("Listener not registered")
        _nite2.niteRegisterUserTrackerCallbacks(self.user_tracker._handle, self._pcallbacks)
        self.user_tracker = None
    
    def _on_ready_for_next_frame(self, cookie):
        self.on_ready_for_next_frame()
    def on_ready_for_next_frame(self):
        pass


@inherit_properties(_nite2.NiteGestureData, "_gesture")
class GestureData(object):
    def __init__(self, gesture):
        self._gesture = gesture

    def is_complete(self):
        return (self.state & _nite2.NiteGestureState.NITE_GESTURE_STATE_COMPLETED) != 0
    def is_in_progress(self):
        return (self.state & _nite2.NiteGestureState.NITE_GESTURE_STATE_IN_PROGRESS) != 0


@inherit_properties(_nite2.NiteHandData, "_handdata")
class HandData(object):
    def __init__(self, handdata):
        self._handdata = handdata
    
    def is_new(self):
        return (self.state & _nite2.NiteHandState.NITE_HAND_STATE_NEW) != 0
    def is_lost(self):
        return self.state == _nite2.NiteHandState.NITE_HAND_STATE_LOST
    def is_tracking(self):
        return (self.state & _nite2.NiteHandState.NITE_HAND_STATE_TRACKED) != 0
    def is_touching_fov(self):
        return (self.state & _nite2.NiteHandState.NITE_HAND_STATE_TOUCHING_FOV) != 0

@inherit_properties(_nite2.NiteHandTrackerFrame, "_frame")
class HandTrackerFrame(HandleObject):
    def __init__(self, hand_tracker_handle, pframe):
        self._hand_tracker_handle = hand_tracker_handle
        self._frame = pframe[0]
        HandleObject.__init__(self, pframe)
        self._depth_frame = None
        self._hands = None
        self._gestures = None
    
    def _close(self):
        _nite2.niteHandTrackerFrameRelease(self._hand_tracker_handle, self._handle)

    @property
    def depth_frame(self):
        if self._depth_frame is None:
            self._depth_frame = openni2.VideoFrame(self._frame.pDepthFrame)
        return self._depth_frame

    @property
    def hands(self):
        if self._hands is None:
            self._hands = [self._frame.pHands[i] for i in range(self._frame.handCount)]
        return self._hands
    
    @property
    def gestures(self):
        if self._gestures is None:
            self._gestures = [self._frame.pGestures[i] for i in range(self._frame.gestureCount)]
        return self._gestures

class HandTracker(HandleObject):
    def __init__(self, device = None):
        self.device = device
        handle = _nite2.NiteHandTrackerHandle()
        if device is None:
            _nite2.niteInitializeHandTracker(ctypes.byref(handle))
        else:
            _nite2.niteInitializeHandTrackerByDevice(device._handle, ctypes.byref(handle))
        HandleObject.__init__(self, handle)
    
    def _close(self):
        _nite2.niteShutdownHandTracker(self._handle)

    def read_frame(self):
        pfrm = ctypes.POINTER(_nite2.NiteHandTrackerFrame)()
        _nite2.niteReadHandTrackerFrame(self._handle, ctypes.byref(pfrm))
        return HandTrackerFrame(self._handle, pfrm)

    def set_smoothing_factor(self, factor):
        _nite2.niteSetHandSmoothingFactor(self._handle, factor)
    def get_smoothing_factor(self):
        factor = ctypes.c_float()
        _nite2.niteGetHandSmoothingFactor(self._handle, ctypes.byref(factor))
        return factor.value
    smoothing_factor = property(get_smoothing_factor, set_smoothing_factor)

    def start_hand_tracking(self, *position):
        new_hand_id = HandId()
        if len(position) == 3:
            position = Point3f(*position)
        _nite2.niteStartHandTracking(self._handle, ctypes.byref(position), ctypes.byref(new_hand_id))
        return new_hand_id
    def stop_hand_tracking(self, handid):
        _nite2.niteStopHandTracking(self._handle, handid)

    def add_listener(self, listener):
        # XXX!!!!
        cbs = _nite2.NiteHandTrackerCallbacks()
        _nite2.niteRegisterHandTrackerCallbacks(self._handle, listener.getCallbacks(), None)
    def remove_listener(self, listener):
        # XXX!!!!
        _nite2.niteUnregisterHandTrackerCallbacks(self._handle, listener.getCallbacks())

    def start_gesture_detection(self, gesture_type):
        _nite2.niteStartGestureDetection(self._handle, gesture_type)
    def stop_gesture_detection(self, gesture_type):
        _nite2.niteStopGestureDetection(self._handle, gesture_type)

    def convertHandCoordinatesToDepth(self, x, y, z):
        outX = ctypes.c_float()
        outY = ctypes.c_float()
        _nite2.niteConvertHandCoordinatesToDepth(self._handle, x, y, z, ctypes.byref(outX), ctypes.byref(outY))
        return outX.value, outY.value
    
    def convertDepthCoordinatesToHand(self, x, y, z):
        outX = ctypes.c_float()
        outY = ctypes.c_float()
        _nite2.niteConvertDepthCoordinatesToHand(self._handle, x, y, z, ctypes.byref(outX), ctypes.byref(outY))
        return outX.value, outY.value

class HandTrackerListener(object):
    def __init__(self):
        self._callbacks = _nite2.NiteHandTrackerCallbacks(readyForNextFrame = self._on_ready_for_next_frame)
        self._pcallbacks = ctypes.pointer(self._callbacks)
        self.hand_tracker = None
    
    def _register(self, hand_tracker):
        if self.hand_tracker is not None:
            raise ValueError("Listener already registered")
        self.hand_tracker = hand_tracker
        _nite2.niteRegisterHandTrackerCallbacks(self.hand_tracker._handle, self._pcallbacks, None)
    def _unregister(self):
        if self.hand_tracker is None:
            raise ValueError("Listener not registered")
        _nite2.niteRegisterHandTrackerCallbacks(self.hand_tracker._handle, self._pcallbacks)
        self.hand_tracker = None
    
    def _on_ready_for_next_frame(self, cookie):
        self.on_ready_for_next_frame()
    def on_ready_for_next_frame(self):
        pass





