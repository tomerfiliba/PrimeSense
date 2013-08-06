import sys
import threading
import logging
import subprocess

logger = logging.getLogger("cmd")

def parallelize(iterator):
    results = {}
    def run(i, func):
        try:
            res = func()
        except Exception:
            results[i] = (False, sys.exc_info())
        else:
            results[i] = (True, res)
    threads = []
    for i, func in enumerate(iterator):
        thd = threading.Thread(target = run, args = (i, func))
        threads.append(thd)
        thd.start()
    for thd in threads:
        thd.join()
    output = [None] * len(threads)
    for i in range(len(threads)):
        succ, obj = results[i]
        if succ:
            output[i] = obj
        else:
            t, v, tb = obj
            raise t, v, tb
    return output

class RemoteCommandError(Exception):
    def __init__(self, host, args, rc, out, err):
        Exception.__init__(self, host, args, rc, out, err)
        self.host = host
        self.args = args
        self.rc = rc
        self.out = out
        self.err = err
    def __str__(self):
        lines = ["%s: %s returned %r" % (self.host, self.args, self.rc)]
        if self.out:
            lines.append(self.out)
        if self.err:
            lines.append(self.err)
        return "\n\n".join(lines)

def remote_run(conn, args, cwd = None, allow_failure = False, env = None):
    proc = conn.modules.subprocess.Popen(args, cwd = None, env = env, 
        stdin = subprocess.PIPE, stderr = subprocess.PIPE, stdout = subprocess.PIPE)
    logger.debug("   Running %r on %s (pid %d)", args, conn._config["connid"], proc.pid)
    out, err = proc.communicate()
    rc = proc.wait()
    logger.debug("      %d: returned %r", proc.pid, rc)
    if not allow_failure and rc != 0:
        logger.error("      stderr: %s", err)
        raise RemoteCommandError(conn._config["connid"], args, rc, out, err)
    return out

