import sys
import os
import time
import socket
import traceback
import logging
import threading
from datetime import datetime
from nose.plugins import Plugin
from srcgen.html import HtmlDocument
from srcgen.js import JS



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
        if status not in ("ok", "skip"):
            self.all_ok = False
    
    def to_html(self, doc):
        if not self.tests:
            return
        with doc.div(class_ = "test_suite" + (" test_suite_all_ok" if self.all_ok else "")):
            with doc.subelem("details"):
                with doc.subelem("summary", class_ = "ok" if self.all_ok else "fail"):
                    doc.span(self.name, class_ = "test_name")
                    doc.span("Module: ", self.filename, class_ = "test_file")
                with doc.table(class_ = "results"):
                    with doc.tr():
                        doc.th("Status")
                        doc.th("Test")
                        doc.th("Duration")
                    for test, dur, res, extra in self.tests:
                        with doc.tr(class_ = res + (" single_test_ok" if res == "ok" else "")):
                            doc.td(res, class_ = "status")
                            with doc.td(class_ = "test_name"):
                                #doc.text("Hello")
                                self._format_details(doc, extra, test)
                            doc.td(self._human_duration(dur), class_="duration")

    def _format_details(self, doc, extra, test):
        if extra:
            with doc.subelem("details"):
                name = (test.shortDescription() or str(test)).split(".")
                with doc.subelem("summary"):
                    doc.strong(name[-1], class_ = "test_name")
                    doc.text("(%s)" % (".".join(name[:-1]),))
                
                if isinstance(extra, list):
                    with doc.table(class_ = "log_records"):
                        for record in extra:
                            level_class = ("log_err" if record.levelno >= logging.ERROR else
                                "log_warn" if record.levelno >= logging.WARNING else "log_info")
                            with doc.tr(class_=level_class):
                                doc.td(datetime.fromtimestamp(record.created).strftime("%H:%M:%S"), class_="log_time")
                                doc.td(record.levelname, class_="log_level")
                                with doc.td(class_="log_msg"):
                                    try:
                                        doc.text(record.msg % record.args if record.args else record.msg)
                                    except Exception:
                                        doc.text(record.msg, record.args)
                else:
                    doc.pre(extra)
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
    
    def begin(self):
        self.records = RecordCollectingHandler()
        self.curr_suite = None
        self.suites = []
        self.start_time = datetime.now()

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
    
    def addSuccess(self, test):
        self.curr_suite.set_result("ok", self.records.records)
    def addError(self, test, err):
        self.curr_suite.set_result("error", "".join(traceback.format_exception(*err)))
    def addFailure(self, test, err):
        self.curr_suite.set_result("fail", "".join(traceback.format_exception(*err)))
    def addSkip(self, test):
        self.curr_suite.set_result("skip")

    def finalize(self, result):
        doc = HtmlDocument()
        with doc.head():
            doc.title("Nose Report")
        
        css = doc.head_css()
        with css("body"):
            css["font-family"] = "arial"
            img = (
                "iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAMAAAAp4XiDAAAAGFBMVEX29vb19fXw8PDy8vL09PTz"
                "8/Pv7+/x8fGKuegbAAAAyUlEQVR42pXRQQ7CMBRDwST9pfe/MahEmgURbt7WmpVb6+vG0dd9REnn"
                "66xRy/qXiCgmEIIJhGACIZhACCYQgvlDCDFIEAwSBIMEwSBBMEgQDBIEgwTBIEEwCJEMQiSDENFM"
                "QmQzCZEbNyGemd6KeGZ6u4hnXe2qbdLHFjhf1XqNLXHev4wdMd9nspiEiWISJgqECQJhgkCYIBAm"
                "CIQJAmGCQJggECYJhAkCEUMEwhCBMEQgDJEIQ2RSg0iEIRJhiB/S+rrjqvXQ3paIJUgPBXxiAAAA"
                "AElFTkSuQmCC"
            )
            css["background"] = 'fixed url(data:image/png;base64,%s)' % (img,)
        
        with css("*:focus"):
            css["outline"] = "none"
        
        with css("summary"):
            css["cursor"] = "pointer"
        
        with css("table"):
            css["width"] = "100%"
        
        with css("div.content"):
            css["margin-right"] = "auto"
            css["margin-left"] = "auto"
            css["max-width"] = "960px"
        
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
                with css(".duration"):
                    css["width"] = "5em"
            
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
                css["background-color"] = "#dd1122"
            
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
        
        with css("div.test_suite"):
            css["border"] = "2px solid #bbb"
            css["padding"] = "5px"
            css["border-radius"] = "5px"
            css["margin-top"] = "2em"
            
            with css("summary"):
                css["padding"] = "5px"
                with css(".ok"):
                    css["background-color"] = "rgb(139, 248, 66)"
                with css(".fail"):
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
                                        doc.strong(" Failures: ")
                                        doc.text(len(result.failures))
                                    with doc.td():
                                        doc.strong(" Errors: ")
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





