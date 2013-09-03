from srcgen.html import HtmlDocument

class Report(object):
    def __init__(self, title, level = 1):
        self.title = title
        self.elements = []
        self.level = level
    def new_section(self, title):
        rep = Report(title, self.level + 1)
        self.elements.append(rep)
        return rep
    def add_succ(self, text, *args):
        text = text % args if args else text
        self.elements.append(("background:#ddffdd;", text))
    def add_error(self, text, *args):
        text = text % args if args else text
        self.elements.append(("background:#ffdddd;", text))
    def add_text(self, text, *args):
        text = text % args if args else text
        self.elements.append(("", text))
    def add_link(self, url, name, style=""):
        self.elements.append((style, (url, name)))

    def _render(self, doc):
        with doc.div(style = "padding-left:%dpx;" % ((self.level-1 * 50),)):
            doc.inline_subelem("h%d" % (self.level,), self.title)
            for elem in self.elements:
                if isinstance(elem, Report):
                    elem._render(doc)
                else:
                    style, text = elem
                    if isinstance(text, tuple):
                        url, name = text
                        doc.a(name, href=url)
                    else:
                        doc.p(text, style=style)

    def render(self):
        doc = HtmlDocument()
        with doc.head():
            doc.title(self.title)
        with doc.body(style="font-size:16px;font-family:sans-serif;"):
            self._render(doc)
        return str(doc)


