#script is meant for storing and loading of permanent data
#permanent data is stored in a dictionary

import os

globalDir = os.path.expanduser("~")+"\AppData\Local\Thoth"

#first time setup, create the directory and all the things in it, if havent.
try:
    os.mkdir(globalDir) #returns an error if directory already exists
    empty = {
        "forbidden" : ['.ini', '.ththscrpt', '.git'],
        "wrongTries" : 0,
    }
    open(globalDir + "\\" + "data.ththscrpt", "w").write(str(empty))
except:
    pass

#get a value from the stored dictionary, if key does not exist, defaultData is returned and stored.
def getData(key, defaultData=None):
    data:dict = eval(open(globalDir + "\\" + "data.ththscrpt", "r").read())
    if key not in data:
        data[key] = defaultData
        open(globalDir + "\\" + "data.ththscrpt", "w").write(str(data))
        return defaultData
    return data[key]

#sets a key value pair to our stored dictionary
def setData(key, value):
    data:dict = eval(open(globalDir + "\\" + "data.ththscrpt", "r").read())
    data[key] = value
    open(globalDir + "\\" + "data.ththscrpt", "w").write(str(data))