#script is meant for storing and loading of permanent data
#permanent data is stored in a dictionary

import os

#globalDir = os.getcwd() + "\savedData" #os.path.expanduser("~")+"\AppData\Local\Thoth"
globalDir = os.path.dirname(os.path.abspath(__file__)) + "\savedData"

def firstTime():
    #first time setup, create the directory and all the things in it, if havent.
    try:
        os.mkdir(globalDir) #returns an error if directory already exists
    except:
        pass
    empty = {
            "forbidden" : ['.ini', '.ththscrpt'],
            "wrongTries" : 0,
        }
    
    open(globalDir + "\\" + "data.ththscrpt", "w").write(str(empty))

#get a value from the stored dictionary, if key does not exist, defaultData is returned and stored.
def getData(key, defaultData=None):
    if not os.path.exists(globalDir + "\\" + "data.ththscrpt"):
        firstTime()
    data:dict = eval(open(globalDir + "\\" + "data.ththscrpt", "r").read())
    if key not in data:
        data[key] = defaultData
        open(globalDir + "\\" + "data.ththscrpt", "w").write(str(data))
        return defaultData
    return data[key]

#sets a key value pair to our stored dictionary
def setData(key, value):
    if not os.path.exists(globalDir + "\\" + "data.ththscrpt"):
        firstTime()
    data:dict = eval(open(globalDir + "\\" + "data.ththscrpt", "r").read())
    data[key] = value
    open(globalDir + "\\" + "data.ththscrpt", "w").write(str(data))