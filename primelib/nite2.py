import os
import ctypes
from primelib import _nite2 as c_api
from primelib import openni2
from primelib.utils import inherit_properties, ClosedHandle, HandleObject, InitializationError
import weakref
import atexit


_default_dll_directories = [".", "C:\\Program Files (x86)\\PrimeSense\\NiTE2\\Redist",
    "C:\\Program Files\\PrimeSense\\NiTE2\\Redist"] 

_nite2_initialized = False
dll_directory = None
def initialize(dll_directories = _default_dll_directories):
    global _nite2_initialized
    global dll_directory
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
            c_api.load_dll("NiTE2")
            c_api.niteInitialize()
        except Exception as ex:
            exceptions.append((dlldir, ex))
        else:
            found = True
            dll_directory = dlldir
            break
    os.chdir(prev)
    if not found:
        raise InitializationError("NiTE2 could not be loaded:\n    %s" % 
            ("\n    ".join("%s: %s" % (dir, ex) for dir, ex in exceptions)),)

    _nite2_initialized = True

def is_initialized():
    return _nite2_initialized

_registered_user_trackers = weakref.WeakSet()
_registered_user_tracker_frames = weakref.WeakSet() 
_registered_hand_trackers = weakref.WeakSet()
_registered_hand_tracker_frames = weakref.WeakSet()

def unload():
    global _nite2_initialized
    if not _nite2_initialized:
        return
    _nite2_initialized = False
    for coll in [_registered_user_tracker_frames, _registered_hand_tracker_frames, _registered_hand_trackers, _registered_user_trackers]:
        for hndl in coll:
            hndl.close()
        coll.clear()
    c_api.niteShutdown()

atexit.register(unload)

def get_version():
    return c_api.niteGetVersion()

Point3f = c_api.NitePoint3f
Plane = c_api.NitePlane
Quaternion = c_api.NiteQuaternion
BoundingBox = c_api.NiteBoundingBox
UserId = c_api.NiteUserId
HandId = c_api.NiteHandId
UserMap = c_api.NiteUserMap
SkeletonJoint = c_api.NiteSkeletonJoint

@inherit_properties(c_api.NitePoseData, "_posedata")
class PoseData(object):
    __slots__ = ["_posedata"]
    def __init__(self, posedata):
        self._posedata = posedata
    def is_held(self):
        return (self.state & c_api.NitePoseState.NITE_POSE_STATE_IN_POSE) != 0
    def is_entered(self):
        return (self.state & c_api.NitePoseState.NITE_POSE_STATE_ENTER) != 0
    def is_exited(self):
        return (self.state & c_api.NitePoseState.NITE_POSE_STATE_EXIT) != 0

@inherit_properties(c_api.NiteSkeleton, "_skeleton")
class Skeleton(object):
    __slots__ = ["_skeleton"]
    def __init__(self, skeleton):
        self._skeleton = skeleton
    def get_joint(self, joint_type):
        return self.joints[type]

@inherit_properties(c_api.NiteUserData, "_userdata")
class UserData(object):
    __slots__ = ["_userdata"]
    def __init__(self, userdata):
        self._userdata = userdata
    def is_new(self):
        return (self.state & c_api.NiteUserState.NITE_USER_STATE_NEW) != 0
    def is_visible(self):
        return (self.state & c_api.NiteUserState.NITE_USER_STATE_VISIBLE) != 0;
    def is_lost(self):
        return (self.state & c_api.NiteUserState.NITE_USER_STATE_LOST) != 0;
    def get_pose(self, posetype):
        return PoseData(self.poses[posetype])

@inherit_properties(c_api.NiteUserTrackerFrame, "_frame")
class UserTrackerFrame(HandleObject):
    __slots__ = ["_frame", "_user_tracker_handle", "_depth_frame", "users", "users_by_id", "__weakref__"]
    def __init__(self, pframe, user_tracker_handle):
        self._frame = pframe[0]
        self._user_tracker_handle = user_tracker_handle
        self._depth_frame = None
        c_api.niteUserTrackerFrameAddRef(user_tracker_handle, pframe)
        HandleObject.__init__(self, pframe)
        self.users = []
        self.users_by_id = {}
        for i in range(self.userCount):
            u = UserData(self.pUser[i])
            self.users.append(u)
            self.users_by_id[u.id] = u
        _registered_user_tracker_frames.add(self)
    
    def _close(self):
        c_api.niteUserTrackerFrameRelease(self._user_tracker_handle, self._handle)
        self._frame = ClosedHandle
        self._user_tracker_handle = ClosedHandle
        del self.users[:]
    
    def get_depth_frame(self):
        if self._depth_frame is None:
            self._depth_frame = openni2.VideoFrame(self.pDepthFrame)
        return self._depth_frame


class _NiteDevStruct(ctypes.Structure):
    _fields_ = [
        ("pPlaybackControl", ctypes.c_void_p),
        ("device", openni2.c_api.OniDeviceHandle),
    ]

class UserTracker(HandleObject):
    def __init__(self, device):
        self._devstruct = _NiteDevStruct()
        self._devstruct.device = device._handle
        handle = c_api.NiteUserTrackerHandle()
        if not device:
            c_api.niteInitializeUserTracker(ctypes.byref(handle))
        else:
            c_api.niteInitializeUserTrackerByDevice(ctypes.byref(self._devstruct), ctypes.byref(handle))
        HandleObject.__init__(self, handle)
        _registered_user_trackers.add(self)
        
    @classmethod
    def open_any(cls):
        return UserTracker(None)

    def _close(self):
        c_api.niteShutdownUserTracker(self._handle)

    def read_frame(self):
        pnf = ctypes.POINTER(c_api.NiteUserTrackerFrame)()
        c_api.niteReadUserTrackerFrame(self._handle, ctypes.byref(pnf))
        return UserTrackerFrame(pnf, self._handle)

    def set_skeleton_smoothing_factor(self, factor):
        return c_api.niteSetSkeletonSmoothing(self._handle, factor)
    def get_skeleton_smoothing_factor(self):
        factor = ctypes.c_float()
        c_api.niteGetSkeletonSmoothing(self._handle, ctypes.byref(factor))
        return factor.value
    skeleton_smoothing_factor = property(get_skeleton_smoothing_factor, set_skeleton_smoothing_factor)

    def start_skeleton_tracking(self, userid):
        c_api.niteStartSkeletonTracking(self._handle, userid)
    def stop_skeleton_tracking(self, userid):
        c_api.niteStopSkeletonTracking(self._handle, userid)
    
    def is_tracking(self, userid):
        c_api.niteIsSkeletonTracking(self._handle, userid)

    def start_pose_detection(self, userid, posetype):
        c_api.niteStartPoseDetection(self._handle, userid, posetype)
    def stop_pose_detection(self, userid, posetype):
        c_api.niteStopPoseDetection(self._handle, userid, posetype)
    def stop_all_pose_detection(self, userid):
        c_api.niteStopAllPoseDetection(self._handle, userid)

    def add_listener(self, listener):
        listener._register(self)
    def remove_listener(self, listener):
        listener._unregister()

    def convert_joint_coordinates_to_depth(self,  x, y, z):
        outX = ctypes.c_float()
        outY = ctypes.c_float()
        c_api.niteConvertJointCoordinatesToDepth(self._handle, x, y, z, ctypes.byref(outX), ctypes.byref(outY))
        return (outX.value, outY.value)
    
    def convert_depth_coordinates_to_joint(self, x, y, z):
        outX = ctypes.c_float()
        outY = ctypes.c_float()
        c_api.niteConvertDepthCoordinatesToJoint(self._handle, x, y, z, ctypes.byref(outX), ctypes.byref(outY))
        return (outX.value, outY.value)


class UserTrackerListener(object):
    def __init__(self):
        self._callbacks = c_api.NiteUserTrackerCallbacks(readyForNextFrame = self._on_ready_for_next_frame)
        self._pcallbacks = ctypes.pointer(self._callbacks)
        self.user_tracker = None
    
    def _register(self, user_tracker):
        if self.user_tracker is not None:
            raise ValueError("Listener already registered")
        self.user_tracker = user_tracker
        c_api.niteRegisterUserTrackerCallbacks(self.user_tracker._handle, self._pcallbacks, None)
    def _unregister(self):
        if self.user_tracker is None:
            raise ValueError("Listener not registered")
        c_api.niteUnregisterUserTrackerCallbacks(self.user_tracker._handle, self._pcallbacks)
        self.user_tracker = None
    
    def _on_ready_for_next_frame(self, cookie):
        self.on_ready_for_next_frame()
    def on_ready_for_next_frame(self):
        pass


@inherit_properties(c_api.NiteGestureData, "_gesture")
class GestureData(object):
    def __init__(self, gesture):
        self._gesture = gesture

    def is_complete(self):
        return (self.state & c_api.NiteGestureState.NITE_GESTURE_STATE_COMPLETED) != 0
    def is_in_progress(self):
        return (self.state & c_api.NiteGestureState.NITE_GESTURE_STATE_IN_PROGRESS) != 0


@inherit_properties(c_api.NiteHandData, "_handdata")
class HandData(object):
    def __init__(self, handdata):
        self._handdata = handdata
    
    def is_new(self):
        return (self.state & c_api.NiteHandState.NITE_HAND_STATE_NEW) != 0
    def is_lost(self):
        return self.state == c_api.NiteHandState.NITE_HAND_STATE_LOST
    def is_tracking(self):
        return (self.state & c_api.NiteHandState.NITE_HAND_STATE_TRACKED) != 0
    def is_touching_fov(self):
        return (self.state & c_api.NiteHandState.NITE_HAND_STATE_TOUCHING_FOV) != 0

@inherit_properties(c_api.NiteHandTrackerFrame, "_frame")
class HandTrackerFrame(HandleObject):
    def __init__(self, hand_tracker_handle, pframe):
        self._hand_tracker_handle = hand_tracker_handle
        self._frame = pframe[0]
        c_api.niteHandTrackerFrameAddRef(hand_tracker_handle, pframe)
        HandleObject.__init__(self, pframe)
        self._depth_frame = None
        self._hands = None
        self._gestures = None
        _registered_hand_tracker_frames.add(self)
    
    def _close(self):
        c_api.niteHandTrackerFrameRelease(self._hand_tracker_handle, self._handle)

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
        self._devstruct = _NiteDevStruct()
        self._devstruct.device = device._handle
        handle = c_api.NiteHandTrackerHandle()
        if device is None:
            c_api.niteInitializeHandTracker(ctypes.byref(handle))
        else:
            c_api.niteInitializeHandTrackerByDevice(ctypes.byref(self._devstruct), ctypes.byref(handle))
        HandleObject.__init__(self, handle)
        _registered_hand_trackers.add(self)
    
    def _close(self):
        c_api.niteShutdownHandTracker(self._handle)

    def read_frame(self):
        pfrm = ctypes.POINTER(c_api.NiteHandTrackerFrame)()
        c_api.niteReadHandTrackerFrame(self._handle, ctypes.byref(pfrm))
        return HandTrackerFrame(self._handle, pfrm)

    def set_smoothing_factor(self, factor):
        c_api.niteSetHandSmoothingFactor(self._handle, factor)
    def get_smoothing_factor(self):
        factor = ctypes.c_float()
        c_api.niteGetHandSmoothingFactor(self._handle, ctypes.byref(factor))
        return factor.value
    smoothing_factor = property(get_smoothing_factor, set_smoothing_factor)

    def start_hand_tracking(self, *position):
        new_hand_id = HandId()
        if len(position) == 3:
            position = Point3f(*position)
        c_api.niteStartHandTracking(self._handle, ctypes.byref(position), ctypes.byref(new_hand_id))
        return new_hand_id
    def stop_hand_tracking(self, handid):
        c_api.niteStopHandTracking(self._handle, handid)

    def add_listener(self, listener):
        listener._register(self)
    def remove_listener(self, listener):
        listener._unregister()

    def start_gesture_detection(self, gesture_type):
        c_api.niteStartGestureDetection(self._handle, gesture_type)
    def stop_gesture_detection(self, gesture_type):
        c_api.niteStopGestureDetection(self._handle, gesture_type)

    def convertHandCoordinatesToDepth(self, x, y, z):
        outX = ctypes.c_float()
        outY = ctypes.c_float()
        c_api.niteConvertHandCoordinatesToDepth(self._handle, x, y, z, ctypes.byref(outX), ctypes.byref(outY))
        return outX.value, outY.value
    
    def convertDepthCoordinatesToHand(self, x, y, z):
        outX = ctypes.c_float()
        outY = ctypes.c_float()
        c_api.niteConvertDepthCoordinatesToHand(self._handle, x, y, z, ctypes.byref(outX), ctypes.byref(outY))
        return outX.value, outY.value
    
    def stop_all_hand_tracking(self):
        c_api.niteStopAllHandTracking(self._handle)
    
    def stop_all_gesture_detection(self):
        c_api.niteStopAllGestureDetection(self._handle)


class HandTrackerListener(object):
    def __init__(self):
        self._callbacks = c_api.NiteHandTrackerCallbacks(readyForNextFrame = self._on_ready_for_next_frame)
        self._pcallbacks = ctypes.pointer(self._callbacks)
        self.hand_tracker = None
    
    def _register(self, hand_tracker):
        if self.hand_tracker is not None:
            raise ValueError("Listener already registered")
        self.hand_tracker = hand_tracker
        c_api.niteRegisterHandTrackerCallbacks(self.hand_tracker._handle, self._pcallbacks, None)
    def _unregister(self):
        if self.hand_tracker is None:
            raise ValueError("Listener not registered")
        c_api.niteUnregisterHandTrackerCallbacks(self.hand_tracker._handle, self._pcallbacks)
        self.hand_tracker = None
    
    def _on_ready_for_next_frame(self, cookie):
        self.on_ready_for_next_frame()
    def on_ready_for_next_frame(self):
        pass

    



