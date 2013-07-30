import rpyc

class Platform(object):
    WIN32 = "WIN32"
    WIN64 = "WIN64"
    LIN32 = "LIN32"
    LIN64 = "LIN64"
    LIN_ARM = "LIN_ARM"
    ANDROID = "ANDROID"
    OSX = "OSX"
    
    _all = [v for k, v in locals().items() if not k.startswith("_")]


class HostInfo(object):
    def __init__(self, hostname, platforms, rpyc_port = 18861):
        if not isinstance(platforms, (tuple, list)):
            platforms = [platforms]
        assert platforms, "No platforms given"
        unknown = set(platforms) - set(Platform._all)
        assert not unknown, "Unknown platforms: %r" % (unknown,)
        self.hostname = hostname
        self.platforms = platforms
        self.rpyc_port = rpyc_port

    def connect(self):
        return rpyc.classic.connect(self.hostname, self.rpyc_port)


build_hosts = [
    #HostInfo("BuildServer", [Platform.WIN32, Platform.WIN64]),
    #HostInfo("sdk32", [Platform.LIN32]),
    HostInfo("sdk64", [Platform.LIN64, Platform.LIN_ARM, Platform.ANDROID]),
    #HostInfo("softwaremac", [Platform.OSX])
]




