import traceback
from nose.plugins import Plugin


class HtmlReportPlugin(Plugin):
    name = 'html-output'
    score = 2 # run late
    
    def __init__(self):
        HtmlReportPlugin.__init__(self)
        self.html = [ '<html><head>',
                      '<title>Test output</title>',
                      '</head><body>' ]
    
    def addSuccess(self, test):
        self.html.append('<span>ok</span>')
        
    def addError(self, test, err):
        err = self.formatErr(err)
        self.html.append('<span>ERROR</span>')
        self.html.append('<pre>%s</pre>' % err)
            
    def addFailure(self, test, err):
        err = self.formatErr(err)
        self.html.append('<span>FAIL</span>')
        self.html.append('<pre>%s</pre>' % err)

    def finalize(self, result):
        self.html.append('<div>')
        self.html.append("Ran %d test%s" %
                         (result.testsRun, result.testsRun != 1 and "s" or ""))
        self.html.append('</div>')
        self.html.append('<div>')
        if not result.wasSuccessful():
            self.html.extend(['<span>FAILED ( ',
                              'failures=%d ' % len(result.failures),
                              'errors=%d' % len(result.errors),
                              ')</span>'])                             
        else:
            self.html.append('OK')
        self.html.append('</div></body></html>')
        for l in self.html:
            self.stream.writeln(l)

    def formatErr(self, err):
        exctype, value, tb = err
        return ''.join(traceback.format_exception(exctype, value, tb))
    
    def setOutputStream(self, stream):
        # grab for own use
        self.stream = stream        
        # return dummy stream
        class dummy:
            def write(self, *arg):
                pass
            def writeln(self, *arg):
                pass
        d = dummy()
        return d

    def startContext(self, ctx):
        try:
            n = ctx.__name__
        except AttributeError:
            n = str(ctx).replace('<', '').replace('>', '')
        self.html.extend(['<fieldset>', '<legend>', n, '</legend>'])
        try:
            path = ctx.__file__.replace('.pyc', '.py')
            self.html.extend(['<div>', path, '</div>'])
        except AttributeError:
            pass

    def stopContext(self, ctx):
        self.html.append('</fieldset>')
    
    def startTest(self, test):
        self.html.extend([ '<div><span>',
                           test.shortDescription() or str(test),
                           '</span>' ])
        
    def stopTest(self, test):
        self.html.append('</div>')





