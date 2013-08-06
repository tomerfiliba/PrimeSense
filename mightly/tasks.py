from mightly.framework import OpenNIBuilder, Host, BuildPlatform, NiteBuilder, CrayolaTester, WrapperBuilder, FirmwareBuilder


buildserver = Host("buildserver", outputs = r"C:\Users\tool.lab\outputs")
sdk32 = Host("sdk32", outputs = "/home/buildserver/outputs")
sdk64 = Host("sdk64", outputs = "/home/buildserver/outputs")
softwaremac = Host("softwaremac", outputs = "/Users/buildserver/outputs")

openni_task = OpenNIBuilder([], hosts = {
#     buildserver : [
#         BuildPlatform("win32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "Final/*.msi"),
#         BuildPlatform("win64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Final/*.msi"),
#     ],
#     sdk32 : [
#         BuildPlatform("linux32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "Final/*.tar.bz2"),
#     ],
#     sdk64 : [
#         BuildPlatform("linux64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Final/*.tar.bz2"),
#         BuildPlatform("arm", ["python", "ReleaseVersion.py", "Arm"], output_pattern = "Final/*.tar.bz2"),
#         BuildPlatform("android", ["python", "ReleaseVersion.py", "android"], output_pattern = "Final/*.tar"),
#         BuildPlatform("src", ["python", "ReleaseOpenSource.py"], output_pattern = "Final/*.tar.bz2"),
#     ],
    softwaremac : [
        BuildPlatform("osx", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Final/*.tar.bz2"),
    ],
})

nite_task = NiteBuilder([openni_task], openni_task = openni_task, hosts = {
    buildserver : [
        BuildPlatform("win32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "Final/*.tar.bz2"),
        BuildPlatform("win64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Final/*.tar.bz2"),
    ],
    sdk32 : [
        BuildPlatform("linux32", ["python", "ReleaseVersion.py", "x86"], output_pattern = "Final/*.tar.bz2"),
    ],
    sdk64 : [
        BuildPlatform("linux64", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Final/*.tar.bz2"),
        BuildPlatform("arm", ["python", "ReleaseVersion.py", "arm"], output_pattern = "Final/*.tar.bz2"),
    ],
    softwaremac : [
        BuildPlatform("osx", ["python", "ReleaseVersion.py", "x64"], output_pattern = "Final/*.tar.bz2"),
    ],
})
 
# wrapper_task = WrapperBuilder([openni_task, nite_task], 
#     openni_task = openni_task, 
#     nite_task = nite_task, 
#     host = sdk64,
# )
#  
# fw_task_eva = FirmwareBuilder([], 
#     host = buildserver
# )
#  
# crayola_task = CrayolaTester([wrapper_task, fw_task_eva], 
#     openni_task = openni_task, 
#     nite_task = nite_task,
#     wrapper_task = wrapper_task, 
#     fw_task = fw_task_eva,
#     hosts = [buildserver, sdk64, sdk32, softwaremac],
# )
#  
#goal = crayola_task

goal = openni_task


if __name__ == "__main__":
    goal.run()





