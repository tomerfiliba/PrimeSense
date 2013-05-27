import os
import ctypes
from primelib import _nite2, openni2
from primelib.utils import inherit_properties, ClosedHandle, HandleObject


def initialize(dll_directory = "."):
    prev = os.getcwd()
    os.chdir(dll_directory)
    _nite2.load_dll("NiTE2")
    _nite2.niteInitialize()
    os.chdir(prev)

def unload():
    _nite2.niteShutdown()

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
    def isLost(self):
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

    def startSkeletonTracking(self, userid):
        _nite2.niteStartSkeletonTracking(self._handle, userid)
    def stopSkeletonTracking(self, userid):
        _nite2.niteStopSkeletonTracking(self._handle, userid)

    def startPoseDetection(self, userid, posetype):
        _nite2.niteStartPoseDetection(self._handle, userid, posetype)
    def stopPoseDetection(self, userid, posetype):
        _nite2.niteStopPoseDetection(self._handle, userid, posetype)

    def addListener(self, pListener):
        # XXX!!!
        _nite2.niteRegisterUserTrackerCallbacks(self._handle, pListener.getCallbacks(), pListener)
    def removeListener(self, pListener):
        # XXX!!!
        _nite2.niteUnregisterUserTrackerCallbacks(self._handle, pListener.getCallbacks())

    def convertJointCoordinatesToDepth(self,  x, y, z):
        outX = ctypes.c_float()
        outY = ctypes.c_float()
        _nite2.niteConvertJointCoordinatesToDepth(self._handle, x, y, z, ctypes.byref(outX), ctypes.byref(outY))
        return (outX.value, outY.value)
    
    def convertDepthCoordinatesToJoint(self, x, y, z):
        outX = ctypes.c_float()
        outY = ctypes.c_float()
        _nite2.niteConvertDepthCoordinatesToJoint(self._handle, x, y, z, ctypes.byref(outX), ctypes.byref(outY))
        return (outX.value, outY.value)


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



'''
/** Snapshot of the Hand Tracker algorithm. It holds all the hands identified at this time, as well as the detected gestures */
class HandTrackerFrameRef
{
public:
    HandTrackerFrameRef() : m_pFrame(NULL), m_handTracker(NULL)
    {}
    ~HandTrackerFrameRef()
    {
        release();
    }

    HandTrackerFrameRef(const HandTrackerFrameRef& other) : m_pFrame(NULL)
    {
        *this = other;
    }
    HandTrackerFrameRef& operator=(const HandTrackerFrameRef& other)
    {
        setReference(other.m_handTracker, other.m_pFrame);
        niteHandTrackerFrameAddRef(m_handTracker, m_pFrame);

        return *this;
    }

    bool isValid() const
    {
        return m_pFrame != NULL;
    }

    void release()
    {
        if (m_pFrame != NULL)
        {
            niteHandTrackerFrameRelease(m_handTracker, m_pFrame);
        }
        m_pFrame = NULL;
        m_handTracker = NULL;
    }

    const Array<HandData>& getHands() const {return m_hands;}
    const Array<GestureData>& getGestures() const {return m_gestures;}

    openni::VideoFrameRef getDepthFrame() const
    {
        return m_depthFrame;
    }

    uint64_t getTimestamp() const {return m_pFrame->timestamp;}
    int getFrameIndex() const {return m_pFrame->frameIndex;}
private:
    friend class HandTracker;

    void setReference(NiteHandTrackerHandle handTracker, NiteHandTrackerFrame* pFrame)
    {
        release();
        m_handTracker = handTracker;
        m_pFrame = pFrame;
        m_depthFrame._setFrame(pFrame->pDepthFrame);

        m_hands.setData(m_pFrame->handCount, (HandData*)m_pFrame->pHands);
        m_gestures.setData(m_pFrame->gestureCount, (GestureData*)m_pFrame->pGestures);
    }

    NiteHandTrackerFrame* m_pFrame;
    NiteHandTrackerHandle m_handTracker;
    openni::VideoFrameRef m_depthFrame;

    Array<HandData> m_hands;
    Array<GestureData> m_gestures;
};

/**
This is the main object of the Hand Tracker algorithm.
Through it all the hands and gestures are accessible.
*/
class HandTracker
{
public:
    class Listener
    {
    public:
        Listener() : m_pHandTracker(NULL)
        {
            m_handTrackerCallbacks.readyForNextFrame = newFrameCallback;
        }
        virtual void onNewFrame(HandTracker&) {}
    private:
        friend class HandTracker;
        NiteHandTrackerCallbacks m_handTrackerCallbacks;
        
        NiteHandTrackerCallbacks& getCallbacks() {return m_handTrackerCallbacks;}

        static void ONI_CALLBACK_TYPE newFrameCallback(void* pCookie)
        {
            Listener* pListener = (Listener*)pCookie;
            pListener->onNewFrame(*pListener->m_pHandTracker);
        }

        void setHandTracker(HandTracker* pHandTracker)
        {
            m_pHandTracker = pHandTracker;
        }
        HandTracker* m_pHandTracker;
    };

    HandTracker() : m_handTrackerHandle(NULL)
    {}
    ~HandTracker()
    {
        destroy();
    }

    Status create(openni::Device* pDevice = NULL)
    {
        if (pDevice == NULL)
        {
            return (Status)niteInitializeHandTracker(&m_handTrackerHandle);
            // Pick a device
        }
        return (Status)niteInitializeHandTrackerByDevice(pDevice, &m_handTrackerHandle);
    }

    void destroy()
    {
        if (isValid())
        {
            niteShutdownHandTracker(m_handTrackerHandle);
            m_handTrackerHandle = NULL;
        }
    }

    /** Get the next snapshot of the algorithm */
    Status readFrame(HandTrackerFrameRef* pFrame)
    {
        NiteHandTrackerFrame *pNiteFrame = NULL;
        Status rc = (Status)niteReadHandTrackerFrame(m_handTrackerHandle, &pNiteFrame);
        pFrame->setReference(m_handTrackerHandle, pNiteFrame);

        return rc;
    }

    bool isValid() const
    {
        return m_handTrackerHandle != NULL;
    }

    /** Control the smoothing factor of the skeleton joints */
    Status setSmoothingFactor(float factor)
    {
        return (Status)niteSetHandSmoothingFactor(m_handTrackerHandle, factor);
    }
    float getSmoothingFactor() const
    {
        float factor;
        Status rc = (Status)niteGetHandSmoothingFactor(m_handTrackerHandle, &factor);
        if (rc != STATUS_OK)
        {
            factor = 0;
        }
        return factor;
    }

    /**
    Request a hand in a specific position, assuming there really is a hand there.
    For instance, the position received from a gesture can be used.
    */
    Status startHandTracking(const Point3f& position, HandId* pNewHandId)
    {
        return (Status)niteStartHandTracking(m_handTrackerHandle, (const NitePoint3f*)&position, pNewHandId);
    }
    /** Inform the algorithm that a specific hand is no longer required */
    void stopHandTracking(HandId id)
    {
        niteStopHandTracking(m_handTrackerHandle, id);
    }

    void addListener(Listener* pListener)
    {
        niteRegisterHandTrackerCallbacks(m_handTrackerHandle, &pListener->getCallbacks(), pListener);
        pListener->setHandTracker(this);
    }
    void removeListener(Listener* pListener)
    {
        niteUnregisterHandTrackerCallbacks(m_handTrackerHandle, &pListener->getCallbacks());
        pListener->setHandTracker(NULL);
    }

    /** Start detecting a specific gesture */
    Status startGestureDetection(GestureType type)
    {
        return (Status)niteStartGestureDetection(m_handTrackerHandle, (NiteGestureType)type);
    }
    /** Stop detecting a specific gesture */
    void stopGestureDetection(GestureType type)
    {
        niteStopGestureDetection(m_handTrackerHandle, (NiteGestureType)type);
    }

    /**
    Hand position is provided in a different set of coordinates than the depth coordinates.
    While the depth coordinates are projective, the hand and gestures are provided in real world coordinates, i.e. number of millimeters from the sensor.
    This function enables conversion from the hand coordinates to the depth coordinates. This is useful, for instance, to match the hand to the depth.
    */
    Status convertHandCoordinatesToDepth(float x, float y, float z, float* pOutX, float* pOutY) const
    {
        return (Status)niteConvertHandCoordinatesToDepth(m_handTrackerHandle, x, y, z, pOutX, pOutY);
    }
    /**
    Hand position is provided in a different set of coordinates than the depth coordinates.
    While the depth coordinates are projective, the hand and gestures are provided in real world coordinates, i.e. number of millimeters from the sensor.
    This function enables conversion from the depth coordinates to the hand coordinates. This is useful, for instance, to allow measurements.
    */
    Status convertDepthCoordinatesToHand(int x, int y, int z, float* pOutX, float* pOutY) const
    {
        return (Status)niteConvertDepthCoordinatesToHand(m_handTrackerHandle, x, y, z, pOutX, pOutY);
    }

private:
    NiteHandTrackerHandle m_handTrackerHandle;
};
'''






















