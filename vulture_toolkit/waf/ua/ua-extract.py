#!/home/vlt-gui/env/bin/python

import glob
import re
import sys


""" Load existing ua """
existing=list()
problem=False
for file in glob.glob ('ua*.txt'):
    with open (file,"r") as f:
        for line in f:
            line = line.rstrip()
            if line not in existing:
                existing.append (line)
            else:
                print("WARNING: Duplicate entry: " + str(line) + "\n")
                problem=True

if problem:
    sys.exit(1)
""" User-Agent string should be at the end of the log string 

"HEAD / HTTP/1.0" 200 293 "-" "-"

"""

prog = re.compile('^.*".*" [0-9]{3} [0-9]+ ".*" "(.*)"$')
done=list()
for file in glob.glob ('./*access*'):
    with open (file,"r") as f:
        for line in f:
            line = line.rstrip()
            m = prog.match (line)
            if m:
                ua=m.group(1)
                if ua not in done:
                    done.append(ua)
                    if ua not in existing:
                        print(ua)

    f.close()


