class Task(object):
    pass
class Worker(object):
    pass

buildserver = Worker("buildserver")
sdk64 = Worker("sdk64")
sdk32 = Worker("sdk32")
softwaremac = Worker("softwaremac")


class BuildOpenNI(Task):
    pass

class BuildOpenNI_x86(BuildOpenNI):
    cmd = ["python", "ReleaseVersion.py", "x86"]

class BuildOpenNI_x64(BuildOpenNI):
    cmd = ["python", "ReleaseVersion.py", "x64"]

class BuildOpenNI_Andorid(BuildOpenNI):
    cmd = ["python", "ReleaseVersion.py", "android"]

class BuildOpenNI_src(BuildOpenNI):
    cmd = ["python", "ReleaseSource.py"]

class BuildOpenNI_mac(BuildOpenNI):
    cmd = ["python", "ReleaseVersion.py", "x64"]


BuildOpenNI_x64([sdk64, buildserver])
BuildOpenNI_x86([sdk32, buildserver])



openni_builds = {
    sdk32 : [BuildOpenNI_x86],
    sdk64 : [BuildOpenNI_x64, BuildOpenNI_Andorid, BuildOpenNI_src],
    buildserver : [BuildOpenNI_x86, BuildOpenNI_x64],
    softwaremac : [BuildOpenNI_x64],
}



























