import time
import os
import traceback
import logging
import threading
from nose.plugins import Plugin
from srcgen.hypertext import (html, strong, body, head, div, p, pre, style, table, td, tr, th, small, title, h1, 
    span, pre, TEXT, a, script, UNESCAPED)
from srcgen.hypertext import Element


class summary(Element): pass
class details(Element): pass


class Suite(object):
    def __init__(self, name, filename):
        self.name = name
        self.filename = filename
        self.tests = []
        self.all_ok = True

    def add_test(self, test):
        self.tests.append([test, time.time(), None, None])

    def set_result(self, status, extra = None):
        self.tests[-1][1] = time.time() - self.tests[-1][1]
        self.tests[-1][2] = status
        self.tests[-1][3] = extra
        if status != "ok":
            self.all_ok = False
    
    def to_html(self):
        if not self.tests:
            return
        with div.test_suite:
            with details:
                with summary(class_ = "ok" if self.all_ok else "fail"):
                    span.test_name(self.name)
                    span.test_file("Module: ", self.filename)
                with table.results(style = "width:100%;"):
                    with tr:
                        th("Status", style = "width:50px;")
                        th("Test")
                        th("Duration", style = "width:100px;")
                    for test, dur, res, extra in self.tests:
                        with tr(class_ = res):
                            td(res)
                            with td:
                                if extra:
                                    with details:
                                        name = (test.shortDescription() or str(test)).split(".")
                                        with summary:
                                            strong(name[-1], style = "padding-right: 20px;")
                                            TEXT("(%s)" % (".".join(name[:-1]),))
                                        pre(extra)
                                else:
                                    TEXT(test.shortDescription() or str(test))
                            
                            td(self._human_duration(dur))
    
    def _human_duration(self, sec):
        if sec < 60:
            return "%.2f sec" % (sec,)
        if sec < 60 * 60:
            return "%d:%2.2f min" % (sec // 60, sec % 60)
        return "%d:%02d:%2.2f min" % (sec // 3600, (sec % 3600) // 60, sec % 60)


class MyMemoryHandler(logging.Handler):
    def __init__(self, logformat, logdatefmt):
        logging.Handler.__init__(self)
        self.setFormatter(logging.Formatter(logformat, logdatefmt))
        self.buffer = []
    def emit(self, record):
        self.buffer.append(self.format(record))
    def flush(self):
        pass # do nothing
    def truncate(self):
        self.buffer = []
    def filter(self, record):
        return True
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['lock']
        return state
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.lock = threading.RLock()


class HtmlReportPlugin(Plugin):
    name = 'html-report'
    
    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)
        parser.add_option("--html-report-file", action="store", default="nose_report.html",
                          dest="report_file", help="File to output HTML report to")
    
    def configure(self, options, config):
        Plugin.configure(self, options, config)
        if not self.enabled: 
            return
        self.report_path = options.report_file
        self.logformat = options.logcapture_format
        self.logdatefmt = options.logcapture_datefmt
        self.loglevel = options.logcapture_level
    
    def begin(self):
        self.handler = MyMemoryHandler(self.logformat, self.logdatefmt)
        self.curr_suite = None
        self.suites = []
        self.start_time = time.asctime()

    def setOutputStream(self, stream):
        print stream
        print dir(stream)
        self.stream = stream 
    
    def startTest(self, test):
        self.curr_suite.add_test(test)

    def beforeTest(self, test):
        # setup our handler with root logger
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, MyMemoryHandler):
                root_logger.handlers.remove(handler)
        root_logger.addHandler(self.handler)
        # to make sure everything gets captured
        loglevel = getattr(self, "loglevel", "NOTSET")
        root_logger.setLevel(getattr(logging, loglevel))
    
    def afterTest(self, test):
        self.handler.truncate()
    
    def addSuccess(self, test):
        self.curr_suite.set_result("ok", "\n".join(self.handler.buffer).strip())
    def addError(self, test, err):
        self.curr_suite.set_result("error", "".join(traceback.format_exception(*err)))
    def addFailure(self, test, err):
        self.curr_suite.set_result("fail", "".join(traceback.format_exception(*err)))
    def addSkip(self, test, err):
        self.curr_suite.set_result("fail")

    def finalize(self, result):
        with html as doc:
            with head():
                title("Nose Report")
                with style:
                    TEXT("body {font-family: arial;}")
                    TEXT("*:focus {outline: none;}")
                    TEXT("summary {cursor: pointer;}")
                    #TEXT("div.infobox {background-color: #f0fff0; padding: ;}")
                    TEXT("table.results td {vertical-align: top;}")
                    TEXT("div.test_suite {border: 2px solid #bbb; padding: 5px; border-radius: 5px;}")
                    TEXT("div.test_suite summary {padding: 5px;}")
                    TEXT("div.test_suite summary.ok {background-color: rgb(139, 248, 66);}")
                    TEXT("div.test_suite summary.fail {background-color: rgb(236, 175, 141);}")
                    TEXT("div.test_suite {margin-top: 2em;}")
                    TEXT("div.test_suite span.test_name {font-weight: bold; font-size: 1.5em;}")
                    TEXT("div.test_suite span.test_file {float: right;}")
                    TEXT("table.results tr.ok {background-color: rgb(139, 248, 66);}")
                    TEXT("table.results tr.fail {background-color: #dddd22;}")
                    TEXT("table.results tr.error {background-color: rgb(236, 175, 141);}")
                    TEXT("table.results tr.skip {background-color: #dd1122;}")
                    TEXT("div.content {margin-right:auto; margin-left:auto; max-width:960px;}")
                    
            
            with body():
                with div.content:
                    h1("Nose Report")
                    with div.infobox:
                        p("Started:", self.start_time)
                        p("Ended:", time.asctime())
                        p("Total of %d tests, %d failures, %d errors" % (result.testsRun, 
                            len(result.failures), len(result.errors)))
                        with script():
                            UNESCAPED("""function toggle_expand(){
                                var all_details = document.getElementsByTagName('details');
                                
                                for(var i = 0; i < all_details.length; i++) {
                                    all_details[i].open = !all_details[i].open;
                                }
                            }""")
                        with p:
                            a("Expand", onclick="toggle_expand()")
            
                    for suite in self.suites:
                        suite.to_html()
        
        with open(self.report_path, "w") as f:
            f.write(str(doc))

    def startContext(self, ctx):
        self.curr_suite = Suite(getattr(ctx, "__name__", str(ctx)), 
            getattr(ctx, "__module__", getattr(ctx, "__file__", "?")))
        self.suites.append(self.curr_suite)





