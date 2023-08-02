#script is meant for directory and file related functions and classes

import os
from os.path import isfile as isFile
import sys
from cryption import *
from saveload import *

from colorama import Fore, Style
import colorama
colorama.init()

# GLOBAL VARIABLES ############################################################################################################################

globalCurrentModificationProgess = 0

# FUNCTIONS ###################################################################################################################################

def joinAddr(string1, string2):
    return string1 + '\\' + string2

illegalExtensions = ['.ini', '.ththscrpt', '.git']
#returns whether a given file is allowed to be seen by Thoth
def isAllowed(filePath:str):
    for extension in illegalExtensions:
        if filePath.endswith(extension):
            return False
    return True

#displays a string representation of an integer size in bytes.
def sizeToString(size:int):
    unit = "B"
    if size >= 1024:
        unit = "KB"
        size = size / 1024
    if size >= 1024:
        unit = "MB"
        size = size / 1024
    if size >= 1024:
        unit = "GB"
        size = size / 1024
    return f"{round(size,3)}{unit}"
    
#the constructor of each class requires two arguments, the parent address and file/directory name.
class File:
    def __init__(self, parentFolder:str, itemName:str):
        self.name = itemName
        self.path = joinAddr(parentFolder, itemName)
    def delete(self):
        try:
            os.remove(self.path)
        except Exception as e:
            print(f"Error deleting file: {e}")
    def getSize(self):
        return os.path.getsize(self.path)
    def modify(self, isEncrypting:bool, key:bytes):
        return modifyFile(isEncrypting, self.path, key)

class Directory:
    def __init__(self, parent:str, itemName:str):
        self.name = itemName;
        self.path = joinAddr(parent, itemName)
        self.contents = []
        totalFileCount = 0
        totalDirCount = 0
        #setting the contents list.
        try:
            for item in os.listdir(self.path):
                fileAddr = joinAddr(self.path, item)
                if not isAllowed(fileAddr):
                    continue #ignore if given fileaddr is not allowed
                if isFile(fileAddr):
                    self.contents.append(File(self.path, item))
                    totalFileCount+=1
                else:
                    addeddir = Directory(self.path, item)
                    self.contents.append(addeddir)
                    totalDirCount+=1
        except:
            print(f"UNABLE TO ACCESS FOLDER WITH PATH: {self.path}")
        self.totalFileCount = totalFileCount
        self.totalDirCount = totalDirCount

    def delete(self):
        try:
            os.rmdir(self.path)
        except Exception as e:
            print(f"Error deleting directory: {e}")
    
    #returns a list of the complete paths of every file within a directory, even within the subdirectories.
    def getCompleteFilePathList(self):
        def fileList(direct:Directory):
            files = list()
            for item in direct.contents:
                itemPath = joinAddr(direct.path, item.name)
                if not isAllowed(itemPath):
                    continue
                if isFile(itemPath):
                    files.append(itemPath)
                else:
                    recursed = fileList(item)
                    files.extend(recursed)
            return files    
        return fileList(self)
    
    def getSize(self):
        totalSize = 0
        for itemPath in self.getCompleteFilePathList():
            totalSize += os.path.getsize(itemPath)
        return totalSize

    #prints out contents into command line
    def printContents(self, nestvalue=0):
        fileCount = 0
        dirCount = 0
        for item in self.contents:
            if isinstance(item, File):
                fileCount += 1
                print(f"{nestvalue * '    '}FILE {fileCount}/{self.totalFileCount}: {item.name} - {sizeToString(item.getSize())}")
            elif isinstance(item, Directory):
                dirCount += 1
                print(f"{nestvalue * '    '}FOLDER {dirCount}/{self.totalDirCount}: {item.name}")
                item.printContents(nestvalue + 1)
        print(f"{nestvalue * '    '}WITHIN {self.name}: {self.totalFileCount} FILES, {self.totalDirCount} FOLDERS - {sizeToString(self.getSize())}")
    
    #encrypt/decrypt every single file in a directory.
    #when encrypting, this function adds another file with extension .tthscrpt in that directory to store an md5 hash of the key used to encrypt it.
    #this is to check whether a key used to decrypt it in the future is the correct one or not.
    #in the same file, we also save the paths of the files that are successfully encrypted.
    #also, every encrypted file will end with a .tth for standardization purposes, explained at cryption.py also
    #!comments related to implementing this naming scheme start with a '!' like this one.
    #function returns a string if there are any errors, None if successful.
    def modifyDirectory(self, isEncrypting:bool, key:bytes, nestvalue:int=0):
        thothInfo = {
            "hash" : None,
            "files" : []
        }

        if isEncrypting:
            #!before we encrypt, check if this folder already contains files encrypted by Thoth.
            #!folders are considered encrypted ONLY when they contain the Thoth script.
            if os.path.exists(joinAddr(self.path, f"{self.name}.ththscrpt")):
                print(f"Folder {self.name} already contains files encrypted by Thoth. To encrypt, decrypt everything in this folder first.")
                return 'ALREADYENCRYPTED'
            #!write the md5 hash of the key into the thoth template
            thothInfo['hash'] = mdHash(key.decode())
        else:
            #!before we decrypt, check if thoth script exists in the given folder.
            if not os.path.exists(joinAddr(self.path, f"{self.name}.ththscrpt")):
                print(f"Folder {self.name} has not been encrypted by Thoth. Not decryptable.")
                return 'UNDECRYPTABLE'
            #!then, check if the given key is correct by checking if the md5 hash of the given key matches the hash in thoth script.
            givenHash = eval(open(joinAddr(self.path, f"{self.name}.ththscrpt"), "r").read())['hash']
            hashKey = mdHash(key.decode())
            if hashKey != givenHash:
                print(f"Wrong key given for folder {self.name}")
                return 'WRONGKEY'

        #we can now modify every single file.
        fileCount = 0
        dirCount = 0
        successCount = self.totalFileCount
        
        for item in self.contents:
            if type(item) == File:
                fileCount+=1
                path = item.modify(isEncrypting, key)
                if type(path) == Exception:
                    successCount-=1
                    print(f"{nestvalue * '    '}FILE {fileCount}/{self.totalFileCount}: {item.name} modification error: {path}")
                else:
                    if isEncrypting:
                        #!append the encrypted paths into the thoth script during encryption process.
                        thothInfo['files'].append(path)
                    global globalCurrentModificationProgess
                    globalCurrentModificationProgess += 1
                    print(f"{nestvalue * '    '}FILE {fileCount}/{self.totalFileCount}: {item.name} successfully modifed.")
            elif type(item) == Directory:
                dirCount+=1
                print(f"{nestvalue * '    '}FOLDER {dirCount}/{self.totalDirCount}: {item.name} opened for modification.")
                item.modifyDirectory(isEncrypting, key, nestvalue+1)
        
        print(f"{nestvalue * '    '}WITHIN {self.name}: {successCount}/{self.totalFileCount} FILES SUCCESSFULLY MODIFIED")
        
        if isEncrypting:
            #!after encryption... we save the data into a thoth script file.
            thothFile = open(joinAddr(self.path, f"{self.name}.ththscrpt"), 'w')
            thothFile.write(str(thothInfo))
        else:
            #!after decryption... we remove the thoth script file entirely, to show that the folder is normal.
            os.remove(joinAddr(self.path, f"{self.name}.ththscrpt"))

#converts a string path to a Directory object
def path2Dir(path:str):
    p = path.split(sep='\\')
    name = p[-1]
    parentPath = path.removesuffix('\\' + name)
    return Directory(parentPath, name)

if __name__ == "__main__":
    inp = input()
    inpl = inp.split(sep=' ')
    print(inpl)

    sampleDirec = path2Dir(inpl[0])
    sampleDirec.printContents()
    
    passw = input()
    key = generateKey(passw)
    sampleDirec.modifyDirectory(True, key)
