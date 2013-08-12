from mightly.framework import (OpenNIBuilder, Host, BuildPlatform, NiteBuilder, CrayolaTester, 
    WrapperBuilder, FirmwareBuilder)


buildserver = Host("buildserver", outputs = r"C:\Users\tool.lab\outputs", installs = r"C:\Users\tool.lab\installs")
sdk32 = Host("sdk32", outputs = "/home/buildserver/outputs", installs = "/home/buildserver/installs")
sdk64 = Host("sdk64", outputs = "/home/buildserver/outputs", installs = "/home/buildserver/installs")
softwaremac = Host("softwaremac", outputs = "/Users/buildserver/outputs", installs = "/Users/buildserver/installs")

openni_task = OpenNIBuilder([], hosts = {
    buildserver : [
        BuildPlatform("win32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "Packaging/Final/*.msi"),
        BuildPlatform("win64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Packaging/Final/*.msi"),
    ],
    sdk32 : [
        BuildPlatform("linux32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "Packaging/Final/*.tar.bz2"),
    ],
    sdk64 : [
        BuildPlatform("linux64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Packaging/Final/*.tar.bz2"),
        BuildPlatform("arm", ["python", "ReleaseVersion.py", "Arm"], output_pattern = "Packaging/Final/*.tar.bz2"),
        BuildPlatform("android", ["python", "ReleaseVersion.py", "android"], output_pattern = "Packaging/Final/*.tar"),
        BuildPlatform("src", ["python", "ReleaseOpenSource.py"], output_pattern = "Packaging/Final/*.tar.bz2"),
    ],
    softwaremac : [
        BuildPlatform("osx", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Packaging/Final/*.tar.bz2"),
    ],
})

nite_task = NiteBuilder([openni_task], hosts = {
    buildserver : [
        BuildPlatform("win32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "SDK/Packaging/Final/*.msi"),
        BuildPlatform("win64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "SDK/Packaging/Final/*.msi"),
    ],
    sdk32 : [
        BuildPlatform("linux32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
    ],
    sdk64 : [
        BuildPlatform("linux64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
        BuildPlatform("arm", ["python", "ReleaseVersion.py", "Arm"], output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
    ],
    softwaremac : [
        BuildPlatform("osx", ["python", "ReleaseVersion.py", "x64"], output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
    ],
})

wrapper_task = WrapperBuilder([openni_task, nite_task], host = sdk64, platform = "linux64")

def FW(name, branch, flag):
    return FirmwareBuilder([], branch = branch,
        hosts = {
            buildserver : [BuildPlatform(name, ["build_server_release.bat", flag, "Release"], None)]
        }
    )

fw_eva_streams = FW("eva_streams", "EvaDevkitDevelop", "EVA_REVC_EVA_STREAMS")
fw_eva_depth_ir = FW("eva_depth_ir", "EvaDevkitDevelop", "EVA_REVC_DEPTH_IR_STREAMS")
fw_eva_motion_control = FW("eva_motion_control", "EvaDevkitDevelop", "EVA_REVC_MOTION_CONTROL")
fw_eva = FW("eva", "EDEV", "EVA")
fw_eva_debug = FW("eva_debug", "EDEV", "EVA_DEBUG")
fw_eva_edev = FW("eva_edev", "EDEV", "EDEV")


crayola_task = CrayolaTester([wrapper_task],
    openni_task = openni_task, 
    nite_task = nite_task,
    wrapper_task = wrapper_task,
    fw_task = None,
    hosts = {
        sdk64 : ["linux64"],
    }
)


if __name__ == "__main__":
    goals = [
        crayola_task,
    ]

    for goal in goals:
        goal.run()





