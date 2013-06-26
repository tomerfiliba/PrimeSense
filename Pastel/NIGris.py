import os
import time
import math
import re

def formatLogAsTable(inStr):
    lines = inStr.split('\n')
    bTable = False
    outStr = ''
    p = re.compile('^\s*([^\t]*)\t([^\t]*)\t([^\t]*)\t([^\t]*)\t(.+)$')
    for line in lines:
        if (line == ''):
            outStr += '<br>'
            continue

        (tableLine, nSubs) = p.subn(r'<tr><td>\1</td><td>\2</td><td>\3</td><td>\4</td><td>\5</td></tr>\n', line)
        if (bTable):
            if (nSubs == 0):
                bTable = False
                outStr += '</table>'
                outStr += line + "<BR>\n"
            else:
                outStr += tableLine
        else:
            if (nSubs == 0):
                outStr += line + "<BR>\n"
            else:
                bTable = True
                outStr += '<table border="1">\n'
                outStr += tableLine
    if (bTable):
        outStr += '</table>'
    return outStr


class HTMLReport(object):
    def start_log(self,path_to_html,name):
        self.path_to_html = path_to_html
        if not os.path.exists(os.path.dirname(path_to_html)):
            os.makedirs(os.path.dirname(path_to_html))
        self.file = open(path_to_html,'w')
        # Construct heading of the report
        self.heading = """<html><body onload="cl_colall()">\n"""
        self.heading += "<H1 align=\"center\" >PASTEL - Test Report</H1>\n<H2 align=\"center\">TestName: %s </H2><H3 align=\"center\">%s</H3>\n"
        self.heading %= (name,time.strftime("%d/%m/%Y %H:%M:%S"))
        self.heading += """
        <style type="text/css">a { text-decoration:none }
        body
        {
        font-size:100%;
        font-family:Serif;
        background-color:#F0FFFF;
        color:#000000;
        margin:10px;

        }
        #loading {
        width: 200px;
        height: 100px;
        background-color: #c0c0c0;
        position: absolute;
        left: 50%;
        top: 50%;
        margin-top: -50px;
        margin-left: -100px;
        text-align: center;
        }

        </style>

        <script>
        var dge=document.getElementById;
                function get_display(a)
                {
          if(!dge)return;
          return document.getElementById(a+'div').style.display;
                }

                function set_display(a, val)
                {
          if(!dge)return;
          document.getElementById(a+'div').style.display = val;
                }

        function cl_expcol(a){
          if(!dge)return;
                  if (get_display(a) == 'none')
                  {
                        set_display(a, 'block');
                  }
                  else
                  {
                    set_display(a, 'none');
                  }
        }

        function cl_colall(){
          if(!dge)return;

          for(i=1;document.getElementById('test'+i);i++){
            set_display('test'+i, 'none');
          }
        }

        function cl_expall(){
          if(!dge)return;

          for(i=1;document.getElementById('test'+i);i++){
            set_display('test'+i, 'block');
          }
        }

        function cl_hidePassed(){
          if(!dge)return;

          for(i=1;i < document.getElementsByTagName('div').length;i++){
            if (document.getElementsByTagName('div')[i].title == "passed")
            {
                  document.getElementsByTagName('div')[i].style.display = 'none';
            }
          }
        }

        function cl_showPassed(){
          if(!dge)return;

          for(i=1;i < document.getElementsByTagName('div').length;i++){
            if (document.getElementsByTagName('div')[i].title == "passed")
            {
              if (document.getElementsByTagName('div')[i].id == "")
              {
                    document.getElementsByTagName('div')[i].style.display = 'block';
              }
            }
          }
        }

       document.write('<div id="loading"><br>Loading Report<br>Please wait...</div>');

    // Created by: Simon Willison | http://simon.incutio.com/
    function addLoadEvent(func) {
      var oldonload = window.onload;
      if (typeof window.onload != 'function') {
        window.onload = func;
      } else {
        window.onload = function() {
          if (oldonload) {
            oldonload();
          }
          func();
        }
      }
    }

    addLoadEvent(function() {
      document.getElementById("loading").style.display="none";
    });

        </script>
        """
        self.heading += """<b><a href=\"javascript:cl_expall();\">Expand All<br></a>"""
        self.heading += """<a href=\"javascript:cl_colall();\">Collapse All<br></a><br>"""
        self.heading += """<a href=\"javascript:cl_hidePassed();\">Hide Passed Tests<br></a>"""
        self.heading += """<a href=\"javascript:cl_showPassed();\">Show Passed Tests<br></a></b>"""

        self.heading += "\n"

        # Write heading to file
        self.file.write(self.heading)
        self.test_results_html = ''
        self.sdk_logs_html = ''
        # number of tests in the report
        self.test_num = 1

    def add(self,passed,test_string,sdk_string,imageBase64list = None):
        """ will add a report to the html"""
        # Check if sdk string is none to prevent exception
        if sdk_string == None:
            sdk_string = ''
        # Assign the apropriate color to the text
        if passed:
            color = "#347C2C"
            pstring = "passed"
        else:
            color = "#FF0000"
            pstring = "failed"

        image_str = ""
        if imageBase64list != None:
            for base64str in imageBase64list:
                image_str += "%s<img src=\"data:image/jpg;base64,%s\" />" % ('  ',base64str)

        # Create the results sections
        temp_res = "<div title=\"%s\"><a title = \"%s\" href=\"javascript:cl_expcol('test%d');\"><font color=\"%s\"><HR>%s</font><br></a></div>\n"
        test_string = test_string.replace("\n","<br>")
        temp_res %= (pstring,pstring,self.test_num,color,test_string)
        # Create the SDK log sections
        temp_sdk = "<a title = \"%s\" id=\"test%d\"><div id=\"test%ddiv\">%s<br>%s</div></a>\n"
        sdk_string = formatLogAsTable(sdk_string)
        temp_sdk %= (pstring,self.test_num,self.test_num,sdk_string,image_str)

        self.file.write(temp_res)
        self.file.write(temp_sdk)
        #self.file.write("<HR>\n")

        # Increase test_num
        self.test_num += 1
        self.file.flush()


    def __del__(self):
        if "file" in dir(self):
            self.file.write("</ol>\n</html>\n</body>")
            self.file.close()


class HTMLIndex(object):
    def __init__(self,path_to_html,name,extra_tag = None,extra_value = None):
        self.path_to_html = path_to_html
        if not os.path.exists(os.path.dirname(path_to_html)):
            os.makedirs(os.path.dirname(path_to_html))
        self.file = open(path_to_html,'w')
        # Construct heading of the report
        self.heading = "<html>\n<body>\n<H1 align=\"center\" >PASTEL - Test Index</H1>\n<H2 align=\"center\">TestList Name: %s </H2><H3 align=\"center\">%s</H3>\n"
        if extra_tag != None and extra_value != None:
            if (type(extra_tag).__name__ == 'str' and type(extra_value).__name__ == 'str'):
                tmpstr = "<H4 align=\"center\"><%s>%s : %s</%s></H4>\n<br>"
                tmpstr %= (extra_tag,extra_tag,extra_value,extra_tag)
                self.heading += tmpstr
            elif (type(extra_tag).__name__ == 'list' and type(extra_value).__name__ == 'list' and len(extra_value) == len(extra_tag)):
                tmpstr = ''
                for i in range(len(extra_tag)):
                    tmpstr += "<H4 align=\"center\"><%s>%s : %s</%s></H4>\n"
                    tmpstr %= (extra_tag[i],extra_tag[i],extra_value[i],extra_tag[i])
                    if i == len(extra_tag) -1:
                        tmpstr += "<br>"



                self.heading += tmpstr




        self.heading %= (name,time.strftime("%d/%m/%Y %H:%M:%S"))
        self.heading += """
        <html>
        <body onload="cl_colall()">
        <style type="text/css">a { text-decoration:none }
        body
        {
        font-size:200%;
        font-family:Serif;
        background-color:#F0FFFF;
        color:#000000;
        margin:10px;

        }

        </style>
        <ol>
        """
        self.file.write(self.heading)
        self.file.flush()


    def format_time(self,milli):

        milli = int(milli)
        seconds = int((math.floor(milli / 1000)) % 60 )
        if seconds < 10:
            seconds = '0' + str(seconds)
        minutes =  int((math.floor (milli / (1000 * 60))) % 60)
        if minutes < 10:
            minutes = '0' + str(minutes)
        hours =  int(math.floor (milli /(1000 * 60 * 60)))
        if hours < 10:
            hours = '0' + str(hours)

        return "%s:%s:%s" %(hours,minutes,seconds)


    def add(self,passed,path_results,name,time = -1):
        """ will add a report to the html"""
        # Assign the apropriate color to the text
        if passed:
            color = "#347C2C"
            pstring = "passed"
        else:
            color = "#FF0000"
            pstring = "failed"

        # Create the results sections

        link = "<a href=\"%s\"><font color=\"%s\"><li>%s<br></li></font></a>\n"

        if (time == -1):
            link %= (path_results,color,name)
        else:
            link %= (path_results,color,self.format_time(time) + " - " + name)


        self.file.write(link)
        self.file.flush()

    def __del__(self):
        if "file" in dir(self):
            self.file.write("</ol>\n</html>\n</body>")
            self.file.close()



if __name__ == "__main__":
    a = HTMLReport()
    a.start_log("./results/tryme.html",'TestKAKI')
    a.add(True,"TestString\n blalblacflasldlasdlasld","SDKLOGS bla \nblagv \nbla lfsd")
    a.add(False,"TestString \nblalblacflasldlasdlasld","SDKLOGS \nbla blagv bl\na lfsd")
    a.add(True,"TestString blalblacfl\nasldlasdlasld","SDKLOGS b\nla blagv bla lfsd")
    a.add(False,"TestString blalblacflasldlas\ndlasld","SDKLOGS bla blagv\n bla lfsd")
    b = HTMLIndex("./index.html",'Nightly',"SVNBuild","12345")
    b.add(True,"./results/tryme.html",'TestKaki')
    b.add(False,"./results/Permutations.html",'TestPUPU')
