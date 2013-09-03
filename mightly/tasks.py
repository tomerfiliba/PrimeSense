from mightly.framework import (OpenNIBuilder, Host, Target, NiteBuilder, CrayolaTester, 
    WrapperBuilder, FirmwareBuilder, Deps, mightly_run)


#=======================================================================================================================
# Hosts
#=======================================================================================================================
buildserver = Host("buildserver", gitbase = r"C:\Users\tool.lab\outputs", 
    installbase = r"C:\Users\tool.lab\installs")
sdk32 = Host("sdk32", gitbase = "/home/buildserver/outputs", 
    installbase = "/home/buildserver/installs")
sdk64 = Host("sdk64", gitbase = "/home/buildserver/outputs", 
    installbase = "/home/buildserver/installs")
softwaremac = Host("softwaremac", gitbase = "/Users/buildserver/outputs", 
    installbase = "/Users/buildserver/installs")

#=======================================================================================================================
# Builders
#=======================================================================================================================
openni_task = OpenNIBuilder(hosts = {
    buildserver : [
        Target("win32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "Packaging/Final/*.msi"),
        Target("win64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Packaging/Final/*.msi"),
    ],
    sdk32 : [
        Target("linux32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "Packaging/Final/*.tar.bz2"),
    ],
    sdk64 : [
        Target("linux64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Packaging/Final/*.tar.bz2"),
        Target("arm", ["python", "ReleaseVersion.py", "Arm"], output_pattern = "Packaging/Final/*.tar.bz2"),
        Target("android", ["python", "ReleaseVersion.py", "android"], output_pattern = "Packaging/Final/*.tar"),
        Target("src", ["python", "ReleaseOpenSource.py"], output_pattern = "Packaging/Final/*.tar.bz2"),
    ],
    softwaremac : [
        Target("osx", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Packaging/Final/*.tar.bz2"),
    ],
})

nite_task = NiteBuilder(Deps(openni_task = openni_task), hosts = {
    buildserver : [
        Target("win32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "SDK/Packaging/Final/*.msi"),
        Target("win64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "SDK/Packaging/Final/*.msi"),
    ],
    sdk32 : [
        Target("linux32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
    ],
    sdk64 : [
        Target("linux64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
        Target("arm", ["python", "ReleaseVersion.py", "Arm"], output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
    ],
    softwaremac : [
        Target("osx", ["python", "ReleaseVersion.py", "x64"], output_pattern = "SDK/Packaging/Final/*.tar.bz2"),
    ],
})

wrapper_task = WrapperBuilder(Deps(openni_task = openni_task, nite_task = nite_task), 
    host = sdk64,         # only a single host is needed to build the wrapper
    target = "linux64",   # use the linux64 headers to compile against
)

#=======================================================================================================================
# Firmware builders
#=======================================================================================================================
def FW(name, branch, flavor):
    return FirmwareBuilder(branch = branch,
        hosts = {
            buildserver : [Target(name, ["build_server_release.bat", flavor, "Release"], 
                output_pattern = "Redist/Release")]
        }
    )

fw_eva_streams = FW("eva_streams", "EvaDevkitDevelop", "EVA_REVC_EVA_STREAMS")
fw_eva_depth_ir = FW("eva_depth_ir", "EvaDevkitDevelop", "EVA_REVC_DEPTH_IR_STREAMS")
fw_eva_motion_control = FW("eva_motion_control", "EvaDevkitDevelop", "EVA_REVC_MOTION_CONTROL")
# fw_eva = FW("eva", "EDEV", "EVA")
# fw_eva_debug = FW("eva_debug", "EDEV", "EVA_DEBUG")
# fw_eva_edev = FW("eva_edev", "EDEV", "EDEV")


#=======================================================================================================================
# Crayola tester
#=======================================================================================================================
crayola_task = CrayolaTester(Deps(
        wrapper_task = wrapper_task, 
        openni_task = openni_task, 
        nite_task = nite_task, 
        fw_task = fw_eva_streams,
    ),
    hosts = {
        # test the following targets on the given hosts, e.g., ``buildserver : ["win32", "win64"]``
        buildserver : ["win64"],
        sdk64 : ["linux64"],
        sdk32 : ["linux32"],
        softwaremac : ["osx"],
    }
)


if __name__ == "__main__":
    mightly_run(crayola_task,
        to_addrs = [
            #"tomerfiliba@gmail.com", 
            "eddie.cohen@primesense.com",
        ],
        #force_build = True,
        #copy_outputs = False,
    )




