class HostInfo(object):
    def __init__(self, hostname, platforms):
        self.hostname = hostname
        self.platforms = platforms

class HostList(object):
    build_server = HostInfo("buildserver", ["WIN32", "WIN64"])
    sdk64 = HostInfo("sdk64", ["LIN64", "Arm", "Android"])
    
    fw_hosts = [build_server]
    test_hosts = [build_server, sdk64]


