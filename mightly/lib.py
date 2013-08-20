import sys
import threading
import logging
import subprocess
from MimeWriter import MimeWriter
from smtplib import SMTP
from cStringIO import StringIO
import os


class HtmlLogHandler(logging.Handler):
    STYLES = {
        "DEBUG" : ["background-color: white"],
        "INFO" : ["background-color: rgba(0, 255, 0, 0.1)"],
        "WARNING" : ["background-color: rgba(255, 255, 0, 0.1)"],
        "ERROR" : ["background-color: rgba(255, 0, 0, 0.1)"],
        "CRITICAL" : ["background-color: rgba(255, 0, 0, 0.4)"],
    }
    
    def __init__(self):
        logging.Handler.__init__(self)
        self._records = []
    def emit(self, record):
        msg = self.format(record)
        self._records.append((record.levelname, msg))
    def to_html(self):
        for level, msg in self._records:
            yield "<pre style='%s; margin: 0;'>%s</pre>" % (";".join(self.STYLES.get(level, ())), 
                msg.replace("&", "&amp").replace("<", "&lt").replace(">", "&gt"))

def parallelize(iterator):
    logger = logging.getLogger("parallelize")
    results = {}
    def run(i, func):
        try:
            res = func()
        except Exception:
            results[i] = (False, sys.exc_info())
            logger.error("Parallel task failed", exc_info = True)
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
    def __init__(self, host, args, cwd, rc, out, err):
        Exception.__init__(self, host, args, cwd, rc, out, err)
        self.host = host
        self.args = args
        self.cwd = cwd
        self.rc = rc
        self.out = out
        self.err = err
    def __str__(self):
        lines = ["%s: %s returned %r (cwd = %r)" % (self.host, self.args, self.rc, self.cwd)]
        if self.out:
            lines.append("stdout:\n    | " + "\n    | ".join(self.out.splitlines()))
        if self.err:
            lines.append("stderr:\n    | " + "\n    | ".join(self.err.splitlines()))
        return "\n".join(lines)

def remote_run(conn, args, cwd = None, allow_failure = False, env = None, logger = None):
    proc = conn.modules.subprocess.Popen(args, cwd = cwd, env = env, 
        stdin = subprocess.PIPE, stderr = subprocess.PIPE, stdout = subprocess.PIPE)
    if not logger:
        logger = logging.getLogger(conn._config["connid"])
    logger.debug("Running %r (pid %d)", " ".join(args), proc.pid)
    out, err = proc.communicate()
    rc = proc.wait()
    if not allow_failure and rc != 0:
        logger.error(">>> %r (%d) exited with %d", " ".join(args), proc.pid, rc)
        if not cwd:
            cwd = conn.modules.os.getcwd()
        else:
            cwd = conn.modules.os.path.abspath(cwd)
        raise RemoteCommandError(conn._config["connid"], args, cwd, rc, out, err)
    return out, err


def sendmail(mailserver, from_addr, to_addrs, subject, text, attachments = ()):
    message = StringIO()
    writer = MimeWriter(message)
    writer.addheader('MIME-Version', '1.0')
    writer.addheader('Subject', subject)
    writer.startmultipartbody('mixed')

    part = writer.nextpart()
    body = part.startbody('text/html')
    body.write(text)

    for fn in attachments:
        part = writer.nextpart()
        part.addheader('Content-Transfer-Encoding', 'base64')
        #if fn.endswith(".htm") or fn.endswith(".html"):
        #    body = part.startbody('text/html; name=%s' % (fn,))
        #else:
        body = part.startbody('text/plain; name=%s' % (os.path.basename(fn),))
        with open(fn, 'rb') as f:
            body.write(f.read().encode("base64"))

    writer.lastpart()

    smtp = SMTP(mailserver)
    smtp.sendmail(from_addr, to_addrs, message.getvalue())
    smtp.quit()



