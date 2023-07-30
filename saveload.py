#script is meant for storing and loading of permanent data

import os

globalDir = os.path.expanduser("~")+"/AppData/Local/Thoth"

#first time setup, create the directory and all the things in it, if havent.
try:
    os.mkdir(globalDir)
    empty = {
        "forbidden" : ['.ini', '.ththscrpt', '.git']
    }
    open(globalDir + "/" + "data.ththscrpt", "w").write(str(empty))
except:
    pass

def getData():
    return open()