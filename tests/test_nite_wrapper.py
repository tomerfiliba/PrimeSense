import os
from primelib import nite2


nite2.initialize()
nite2.get_version()

os.chdir(nite2.loaded_dll_directory)

#dev = openni2.Device.open_any()
#print dev
#ut = nite2.UserTracker(dev)
ut = nite2.UserTracker.open_any()

print ut
frm = ut.read_frame()
print frm
print frm.users
print frm.get_depth_frame()

ht = nite2.HandTracker.open_any()
print ht
frm2 = ht.read_frame()
print frm2


nite2.unload()

