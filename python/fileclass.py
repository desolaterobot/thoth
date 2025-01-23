#script is meant for directory and file related functions and classes

from cryption import *
import os
from os.path import isfile as isFile
import sys
from tkinter import messagebox

from colorama import Fore, Style
import colorama
colorama.init()

# FUNCTIONS ###################################################################################################################################

def joinAddr(string1, string2):
    return string1 + '\\' + string2

#returns whether a given file is allowed to be seen by Thoth
def isAllowed(filePath:str):
    for extension in saveload.getData('forbidden'):
        if filePath.endswith(extension):
            return False
    return True

#displays a string representation of an integer size in bytes.
def sizeToString(size:int, precision:int=2):
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
    if precision == 0:
        return f"{round(size)}{unit}"
    return f"{round(size, precision)}{unit}"
    
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

rootDirectoryFilePathList = []

class Directory:
    def __init__(self, parent:str, itemName:str):
        self.name = itemName;
        self.path = joinAddr(parent, itemName)
        self.contents = []
        totalFileCount = 0
        totalDirCount = 0

        #only applies if the current directory is an encrypted one
        self.isEncrypted = False
        self.encryptionMethod = None
        self.encryptionHash = None

        try:
            for item in os.listdir(self.path):
                fileAddr = joinAddr(self.path, item)
                #! if folder contains a .ththscrpt file, it is evidence that the folder is encrypted by Thoth.
                if fileAddr.endswith('.ththscrpt'):
                    with open(fileAddr, "r") as file:
                        try:
                            self.isEncrypted = True
                            thth_contents = eval(file.read())
                            self.encryptionMethod = thth_contents['method']
                            self.encryptionHash = thth_contents['hash']
                        except:
                            messagebox.showerror('Parsing Error', f'The THTHSCRPT file located in this folder seems to have the wrong configuration.')
                if fileAddr.endswith('.thth'):
                    self.containsEncryptedFiles = True
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
            messagebox.showwarning(f"Error accessing {self.name}", f"{self.path}\nseems to be inaccessible, most likely due to a permission error. This folder will be treated as empty. If you want these files encrypted, move them to another folder.")
        self.totalFileCount = totalFileCount
        self.totalDirCount = totalDirCount

    #delete this directory
    def delete(self):
        try:
            os.rmdir(self.path)
        except Exception as e:
            print(f"Error deleting directory: {e}")
    
    #recursive approach of getting ONLY the COMPLETE filecount of the directory. nothing else, just the number
    def getCompleteFileCount(self)->int:
        if hasattr(self, 'completeFilePathList'):
            return len(self.completeFilePathList)
        def getCFC(directory: Directory):
            if directory.totalDirCount == 0:
                return directory.totalFileCount
            else:
                dirList = []
                for item in directory.contents:
                    if isinstance(item, Directory):
                        dirList.append(item)
                #dirList is a list of directories contained within current directory
                childrenTotal = 0
                for folder in dirList:
                    childrenTotal += getCFC(folder)
                return childrenTotal + directory.totalFileCount
        return getCFC(self)
    

    #returns a list of the complete paths of every file within a directory, even within the subdirectories.
    def getCompleteFilePathList(self)->list:
        if hasattr(self, 'completeFilePathList'):
            return self.completeFilePathList
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
        flist = fileList(self)
        self.completeFilePathList = flist
        return flist

    #returns a list of the complete paths of each subfolder inside the current folder.
    def getCompleteFolderPathList(self):
        if hasattr(self, 'filePathList'):
            return self.filePathList
        def folderlist(direct:Directory):
            folders = list()
            for item in direct.contents:
                itemPath = joinAddr(direct.path, item.name)
                if not isFile(itemPath):
                    folders.append(itemPath)
                    recursed = folderlist(item)
                    folders.extend(recursed)
            return folders    
        return folderlist(self)

    #get size of current folder.
    def getSize(self):
        if hasattr(self, 'size'):
            return self.size
        totalSize = 0
        for itemPath in self.getCompleteFilePathList():
            totalSize += os.path.getsize(itemPath)
        self.size = totalSize
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
            "hash" : None
        }
        if isEncrypting:
            #!before we encrypt, check if this folder already contains files encrypted by Thoth.
            #!folders are considered encrypted ONLY when they contain the Thoth script.
            if os.path.exists(joinAddr(self.path, f"{self.name}.ththscrpt")):
                print(f"Folder {self.name} already contains files encrypted by Thoth. To encrypt, decrypt everything in this folder first.")
                return 'ALREADYENCRYPTED'
            #!write the md5 hash of the key into the thoth template
            thothInfo['hash'] = md5(key.decode())
        else:
            #!before we decrypt, check if thoth script exists in the given folder.
            if not os.path.exists(joinAddr(self.path, f"{self.name}.ththscrpt")):
                print(f"Folder {self.name} has not been encrypted by Thoth. Not decryptable.")
                return 'UNDECRYPTABLE'
            givenHash = eval(open(joinAddr(self.path, f"{self.name}.ththscrpt"), "r").read())['hash']
            hashKey = md5(key.decode())
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
    direct =  Directory(parentPath, name)
    return direct