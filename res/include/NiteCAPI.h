/*******************************************************************************
*                                                                              *
*   PrimeSense NiTE 2.0                                                        *
*   Copyright (C) 2012 PrimeSense Ltd.                                         *
*                                                                              *
*******************************************************************************/

#include <OniPlatform.h>
#include <OniCAPI.h>
#include "NiteCTypes.h"
#include "NiteVersion.h"

#ifdef NITE_EXPORTS
#define NITE_API ONI_C_API_EXPORT
#else
#define NITE_API ONI_C_API_IMPORT
#endif

// General
NITE_API NiteStatus niteInitialize();
NITE_API void niteShutdown();

NITE_API NiteVersion niteGetVersion();

// UserTracker
NITE_API NiteStatus niteInitializeUserTracker(NiteUserTrackerHandle* phandle);
NITE_API NiteStatus niteInitializeUserTrackerByDevice(void* devhandle, NiteUserTrackerHandle* phandle);
NITE_API NiteStatus niteShutdownUserTracker(NiteUserTrackerHandle handle);

NITE_API NiteStatus niteStartSkeletonTracking(NiteUserTrackerHandle handle, NiteUserId user);
NITE_API void niteStopSkeletonTracking(NiteUserTrackerHandle handle, NiteUserId user);
NITE_API bool niteIsSkeletonTracking(NiteUserTrackerHandle handle, NiteUserId user);

NITE_API NiteStatus niteSetSkeletonSmoothing(NiteUserTrackerHandle handle, float factor);
NITE_API NiteStatus niteGetSkeletonSmoothing(NiteUserTrackerHandle handle, float* factor);

NITE_API NiteStatus niteStartPoseDetection(NiteUserTrackerHandle handle, NiteUserId user, NitePoseType pose);
NITE_API void niteStopPoseDetection(NiteUserTrackerHandle handle, NiteUserId user, NitePoseType pose);
NITE_API void niteStopAllPoseDetection(NiteUserTrackerHandle handle, NiteUserId user);

NITE_API NiteStatus niteRegisterUserTrackerCallbacks(NiteUserTrackerHandle handle, NiteUserTrackerCallbacks* callbacks, void* cookie);
NITE_API void niteUnregisterUserTrackerCallbacks(NiteUserTrackerHandle handle, NiteUserTrackerCallbacks* callbacks);

NITE_API NiteStatus niteReadUserTrackerFrame(NiteUserTrackerHandle handle, NiteUserTrackerFrame** frame);

NITE_API NiteStatus niteUserTrackerFrameAddRef(NiteUserTrackerHandle handle, NiteUserTrackerFrame* frame);
NITE_API NiteStatus niteUserTrackerFrameRelease(NiteUserTrackerHandle handle, NiteUserTrackerFrame* frame);

// HandTracker
NITE_API NiteStatus niteInitializeHandTracker(NiteHandTrackerHandle* handle);
NITE_API NiteStatus niteInitializeHandTrackerByDevice(void* devhandle, NiteHandTrackerHandle* handle);
NITE_API NiteStatus niteShutdownHandTracker(NiteHandTrackerHandle handle);

NITE_API NiteStatus niteStartHandTracking(NiteHandTrackerHandle handle, const NitePoint3f* point, NiteHandId* pNewHandId);
NITE_API void niteStopHandTracking(NiteHandTrackerHandle handle, NiteHandId hand);
NITE_API void niteStopAllHandTracking(NiteHandTrackerHandle handle);

NITE_API NiteStatus niteSetHandSmoothingFactor(NiteHandTrackerHandle handle, float factor);
NITE_API NiteStatus niteGetHandSmoothingFactor(NiteHandTrackerHandle handle, float* factor);

NITE_API NiteStatus niteRegisterHandTrackerCallbacks(NiteHandTrackerHandle handle, NiteHandTrackerCallbacks* callbacks, void* cookie);
NITE_API void niteUnregisterHandTrackerCallbacks(NiteHandTrackerHandle handle, NiteHandTrackerCallbacks* callbacks);

NITE_API NiteStatus niteReadHandTrackerFrame(NiteHandTrackerHandle handle, NiteHandTrackerFrame** frame);

NITE_API NiteStatus niteHandTrackerFrameAddRef(NiteHandTrackerHandle handle, NiteHandTrackerFrame* frame);
NITE_API NiteStatus niteHandTrackerFrameRelease(NiteHandTrackerHandle handle, NiteHandTrackerFrame* frame);

NITE_API NiteStatus niteStartGestureDetection(NiteHandTrackerHandle handle, NiteGestureType gesture);
NITE_API void niteStopGestureDetection(NiteHandTrackerHandle handle, NiteGestureType gesture);
NITE_API void niteStopAllGestureDetection(NiteHandTrackerHandle handle);

NITE_API NiteStatus niteConvertJointCoordinatesToDepth(NiteUserTrackerHandle userTracker, float x, float y, float z, float* pX, float* pY);
NITE_API NiteStatus niteConvertDepthCoordinatesToJoint(NiteUserTrackerHandle userTracker, int x, int y, int z, float* pX, float* pY);
NITE_API NiteStatus niteConvertHandCoordinatesToDepth(NiteHandTrackerHandle handTracker, float x, float y, float z, float* pX, float* pY);
NITE_API NiteStatus niteConvertDepthCoordinatesToHand(NiteHandTrackerHandle handTracker, int x, int y, int z, float* pX, float* pY);

