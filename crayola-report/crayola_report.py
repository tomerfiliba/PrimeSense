import sys
import os
import time
import socket
import traceback
import logging
import threading
import shutil
from datetime import datetime
from nose.plugins import Plugin
from srcgen.html import HtmlDocument
from srcgen.js import JS
from nose.plugins.skip import SkipTest
from unittest.case import SkipTest as UTSkipTest 
try:
    import psutil
except ImportError:
    psutil = None


class Suite(object):
    def __init__(self, name, filename):
        self.name = name
        self.filename = filename
        self.tests = []
        self.general_status = "ok"

    def add_test(self, test):
        test._html_start_time = time.time()
        test._html_end_time = time.time()
        test._html_status = "skip"
        test._html_extra = None
        test._html_cpumem = None
        test._html_errlink = ()
        self.tests.append(test)

    def set_result(self, test, status, extra = None):
        if not self.tests:
            test._html_start_time = time.time()
            test._html_end_time = time.time()
            test._html_status = "skip"
            test._html_extra = None
            test._html_cpumem = None
            test._html_errlink = ()
            self.tests.append(test)
        
        test._html_end_time = time.time()
        test._html_status = status
        test._html_extra = extra
        if psutil:
            proc = psutil.Process(os.getpid())
            test._html_cpumem = (proc.get_cpu_percent(), proc.get_memory_percent())
        
        statuses = ["error", "fail", "skip", "ok"]
        self.general_status = min(self.general_status, status, key = statuses.index)
    
    def to_html(self, doc):
        if not self.tests:
            return
        with doc.div(class_ = "test_suite" + (" test_suite_all_ok" if self.general_status == "ok" else "")):
            with doc.subelem("details"):
                with doc.subelem("summary", class_ = self.general_status):
                    doc.span(self.name, class_ = "test_name")
                    doc.span("Module: ", self.filename, class_ = "test_file")
                with doc.table(class_ = "results"):
                    with doc.tr():
                        doc.th("Status")
                        doc.th("Test")
                        doc.th("CPU/Mem")
                        doc.th("Duration")
                    for test in self.tests:
                        res = test._html_status
                        with doc.tr(class_ = res + (" single_test_ok" if res == "ok" else "")):
                            doc.td(res, class_ = "status")
                            with doc.td(class_ = "test_name"):
                                self._format_details(doc, test)
                            with doc.td(class_="cpumem"):
                                if test._html_cpumem:
                                    cpu, mem = test._html_cpumem
                                    doc.text("%.2f%% / %.2f%%" % (cpu, mem))
                            doc.td(self._human_duration(test._html_end_time - test._html_start_time), class_="duration")

    def _format_details(self, doc, test):
        if test._html_extra:
            with doc.subelem("details"):
                name = (test.shortDescription() or str(test)).split(".")
                with doc.subelem("summary"):
                    doc.strong(name[-1], class_ = "test_name")
                    doc.text("(%s)" % (".".join(name[:-1]),))
                
                if isinstance(test._html_extra, list):
                    with doc.table(class_ = "log_records"):
                        for record in test._html_extra:
                            level_class = ("log_err" if record.levelno >= logging.ERROR else
                                "log_warn" if record.levelno >= logging.WARNING else "log_info")
                            with doc.tr(class_ = level_class):
                                doc.td(datetime.fromtimestamp(record.created).strftime("%H:%M:%S"), class_="log_time")
                                doc.td(record.levelname, class_="log_level")
                                with doc.td(class_="log_msg"):
                                    try:
                                        doc.text(record.msg % record.args if record.args else record.msg)
                                    except Exception:
                                        doc.text(record.msg, record.args)
                else:
                    doc.pre(test._html_extra)
                if test._html_errlink:
                    with doc.div(class_ = "log_link"):
                        with doc.ol():
                            for name, url in test._html_errlink:
                                with doc.li():
                                    doc.span("Link to %s: " % (name,))
                                    #url2 = url if "://" in url else "file:///%s" % (url.replace("\\", "/"),)
                                    doc.a(url, href = url.replace("\\", "/"))
        else:
            name = (test.shortDescription() or str(test)).split(".")
            doc.strong(name[-1], class_ = "test_name")
            doc.text("(%s)" % (".".join(name[:-1]),))
        
    def _human_duration(self, sec):
        if sec < 60:
            return "%.2f sec" % (sec,)
        if sec < 60 * 60:
            return "%d:%2.2f min" % (sec // 60, sec % 60)
        return "%d:%02d:%2.2f min" % (sec // 3600, (sec % 3600) // 60, sec % 60)


class RecordCollectingHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.records = []
    def emit(self, record):
        self.records.append(record)
    def flush(self):
        pass
    def clear(self):
        self.records = []
    def filter(self, record):
        return True
    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop('lock')
        return state
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.lock = threading.RLock()


class HtmlReportPlugin(Plugin):
    name = 'crayola-report'
    score = 30000
    
    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)
        parser.add_option("--html-report-file", action="store", default="nose_report.html",
                          dest="report_file", help="File to output HTML report to")
    
    def configure(self, options, config):
        Plugin.configure(self, options, config)
        if not self.enabled: 
            return
        self.report_path = options.report_file
    
    def begin(self):
        self.records = RecordCollectingHandler()
        self.curr_suite = None
        self.suites = []
        self.start_time = datetime.now()
        self.num_skips = 0
        self.report_log_dir = os.path.join(os.path.dirname(os.path.abspath(self.report_path)), "nose-logs")
        shutil.rmtree(self.report_log_dir, ignore_errors = True)
        os.mkdir(self.report_log_dir)

    def startTest(self, test):
        self.curr_suite.add_test(test)

    def beforeTest(self, test):
        # setup our handler with root logger
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, RecordCollectingHandler):
                root_logger.handlers.remove(handler)
        root_logger.addHandler(self.records)
        # to make sure everything gets captured
        root_logger.setLevel(logging.INFO)
    
    def afterTest(self, test):
        self.records.clear()
    
    def copy_logs(self, paths):
        outputs = []
        for name, path in paths:
            shutil.copy(path, self.report_log_dir)
            outputs.append((name, "nose-logs/%s" % (os.path.basename(path),)))
        return outputs
    
    def addSuccess(self, test):
        try:
            test._html_errlink = getattr(test.test.inst, "report_error_links", ())
        except AttributeError:
            test._html_errlink = ()
        test._html_errlink = self.copy_logs(test._html_errlink)
        self.curr_suite.set_result(test, "ok", self.records.records)
    
    def addError(self, test, err):
        try:
            test._html_errlink = getattr(test.test.inst, "report_error_links", ())
        except AttributeError:
            test._html_errlink = ()
        test._html_errlink = self.copy_logs(test._html_errlink)
        if issubclass(err[0], (SkipTest, UTSkipTest)):
            self.num_skips += 1
            self.curr_suite.set_result(test, "skip", self.records.records)
        else:
            self.curr_suite.set_result(test, "error", "".join(traceback.format_exception(*err)))
    
    def addFailure(self, test, err):
        try:
            test._html_errlink = getattr(test.test.inst, "report_error_links", ())
        except AttributeError:
            test._html_errlink = ()
        test._html_errlink = self.copy_logs(test._html_errlink)
        self.curr_suite.set_result(test, "fail", "".join(traceback.format_exception(*err)))

    def finalize(self, result):
        doc = HtmlDocument()
        with doc.head():
            doc.title("Nose Report")
        
        css = doc.head_css()
        with css("body"):
            css["font-family"] = "arial"
            #img = (
            #    "iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAMAAAAp4XiDAAAAGFBMVEX29vb19fXw8PDy8vL09PTz"
            #    "8/Pv7+/x8fGKuegbAAAAyUlEQVR42pXRQQ7CMBRDwST9pfe/MahEmgURbt7WmpVb6+vG0dd9REnn"
            #    "66xRy/qXiCgmEIIJhGACIZhACCYQgvlDCDFIEAwSBIMEwSBBMEgQDBIEgwTBIEEwCJEMQiSDENFM"
            #    "QmQzCZEbNyGemd6KeGZ6u4hnXe2qbdLHFjhf1XqNLXHev4wdMd9nspiEiWISJgqECQJhgkCYIBAm"
            #    "CIQJAmGCQJggECYJhAkCEUMEwhCBMEQgDJEIQ2RSg0iEIRJhiB/S+rrjqvXQ3paIJUgPBXxiAAAA"
            #    "AElFTkSuQmCC"
            #)
            #css["background"] = 'fixed url(data:image/png;base64,%s)' % (img,)
            css["background-color"] = "#f1f1f1";
        
        with css("*:focus"):
            css["outline"] = "none"
        
        with css("summary"):
            css["cursor"] = "pointer"
        
        with css("table"):
            css["width"] = "100%"
        
        with css("div.content"):
            css["margin-right"] = "auto"
            css["margin-left"] = "auto"
            css["max-width"] = "1200px"
        
        with css("table.results"):
            with css("td"):
                css["vertical-align"] = "top"
                css["padding-top"] = "5px"
                with css(".status"):
                    css["text-align"] = "center"
                    css["font-weight"] = "bold"
                    css["width"] = "4em"
                with css(".test_name"):
                    css["padding-top"] = "0"
                    css["max-width"] = "1030px"
                    css["overflow-x"] = "auto"
                with css(".duration"):
                    css["width"] = "5em"
                with css(".cpumem"):
                    css["width"] = "4em"
                    css["font-size"] = "smaller"
            
            with css("summary strong.test_name"):
                css["padding-right"] = "3em"
            with css("details pre"):
                css["background"] = "rgba(255,255,255,0.8)"
                css["padding"] = "1em"
                css["border-radius"] = "5px"
                        
            with css("tr.ok"):
                css["background-color"] = "rgb(139, 248, 66)"
            with css("tr.fail"):
                css["background-color"] = "rgb(236, 175, 141)"
            with css("tr.error"):
                css["background-color"] = "rgb(236, 141, 141);"
            with css("tr.skip"):
                css["background-color"] = "#C9BB87"
            
            with css("table.log_records"):
                css["font-family"] = "monospace"
                css["padding"] = "1em"
                css["border-radius"] = "5px"
                css["background-color"] = "rgba(255,255,255,0.8)"
                css["margin-bottom"] = "1em"
                
                with css("tr"):
                    with css(".log_err"):
                        css["background-color"] = "rgba(255,0,0,0.3)"
                    with css(".log_warn"):
                        css["background-color"] = "rgba(255,255,0,0.5)"
                
                with css("td.log_time"):
                    css["width"] = "5em"
                with css("td.log_level"):
                    css["width"] = "5em"
            
            with css("div.log_link"):
                css["margin-bottom"] = "1em"
                css["padding"] = "1em"
                css["background-color"] = "rgba(255,255,255,0.8)"
                css["border-radius"] = "5px"
                
                with css("ol"):
                    css["list-style-type"] = "none"
                    css["margin"] = "0"
                    css["padding"] = "0"
        
        with css("div.test_suite"):
            css["border"] = "2px solid #bbb"
            css["padding"] = "5px"
            css["border-radius"] = "5px"
            css["margin-top"] = "2em"
            
            with css("summary"):
                css["padding"] = "5px"
                with css(".ok"):
                    css["background-color"] = "rgb(139, 248, 66)"
                with css(".skip"):
                    css["background-color"] = "#C9BB87"
                with css(".fail"):
                    css["background-color"] = "rgb(236, 175, 141)"
                with css(".error"):
                    css["background-color"] = "rgb(236, 175, 141)"
            with css("span.test_name"):
                css["font-weight"] = "bold"
                css["font-size"] = "1.5em"
            with css("span.test_file"):
                css["float"] = "right"
        
        with doc.body():
            with doc.div(class_ = "content"):
                doc.h1("Nose Report")
                with doc.div(class_ = "infobox"):
                    with doc.table():
                        with doc.tr():
                            with doc.td():
                                doc.strong("Started: ")
                                doc.code(self.start_time)
                            with doc.td():
                                doc.strong("Ended: ")
                                doc.code(datetime.now())
                        with doc.tr():
                            with doc.td():
                                doc.strong("Hostname: ")
                                doc.code(socket.gethostname())
                            with doc.td():
                                doc.strong("Workdir: ")
                                doc.code(os.getcwd())
                        with doc.tr():
                            with doc.td(colspan=2):
                                doc.code(" ".join(sys.argv))
                        
                        with doc.tr():
                            with doc.td():
                                with doc.table(), doc.tr():
                                    with doc.td():
                                        doc.strong("Tests: ")
                                        doc.text(result.testsRun)
                                    with doc.td():
                                        doc.strong("Skips: ")
                                        doc.text(self.num_skips)
                                    with doc.td():
                                        doc.strong("Failures: ")
                                        doc.text(len(result.failures))
                                    with doc.td():
                                        doc.strong("Errors: ")
                                        doc.text(len(result.errors))
                                
                            with doc.td():
                                with doc.script():
                                    m = JS()
                                    with m.func("toggle_expand"):
                                        m.var("btn", "document.getElementById('toggle_expand')")
                                        m.var("show", "btn.textContent.indexOf('Expand') >= 0")
                                        m.var("all_details", "document.getElementsByTagName('details')")
                                        with m.for_("var i = 0", "i < all_details.length", "i++"):
                                            m.stmt("all_details[i].open = show")
                                        m.stmt('btn.textContent = show ? "Collapse All" : "Expand All"') 
                                    
                                    with m.func("toggle_success", "state"):
                                        m.var("btn", "document.getElementById('toggle_successful')")
                                        m.var("show", "btn.textContent.indexOf('Show') >= 0")
                                        m.var("all_suites", "document.getElementsByClassName('test_suite_all_ok')")
                                        with m.for_("var i = 0", "i < all_suites.length", "i++"):
                                            m.stmt("all_suites[i].hidden = !show")
                                        m.var("all_singles", "document.getElementsByClassName('single_test_ok')")
                                        with m.for_("var i = 0", "i < all_singles.length", "i++"):
                                            m.stmt("all_singles[i].hidden = !show")
                                        m.stmt('btn.textContent = show ? "Hide Success" : "Show Success"') 

                                    doc.raw(str(m))
                                doc.button("Expand All", style="width:9em;", id="toggle_expand", onclick="toggle_expand()")
                                doc.button("Hide Success", style="width:9em;", id="toggle_successful", onclick="toggle_success()")
        
                for suite in self.suites:
                    suite.to_html(doc)
                
                doc.p()
                doc.p()
        
        with open(self.report_path, "w") as f:
            f.write(doc.render(" "))

    def startContext(self, ctx):
        self.curr_suite = Suite(getattr(ctx, "__name__", str(ctx)), 
            getattr(ctx, "__module__", getattr(ctx, "__file__", "?")))
        self.suites.append(self.curr_suite)





