#script is for encryption and hash related functions

import saveload
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import hashlib
import tkinter as tk
from tkinter import ttk
from math import ceil
import string

globalCurrentFileBeingModified = ""
charList = string.digits + string.ascii_letters + "()_-"
d = {}
for index, char in enumerate(charList):
    d[str(char)] = index
charMap = d
charNum = len(charList)

#filename-safe ceasar cipher
class Caesar():
    def __init__(self, key:bytes):
        self.key = sha256(key.decode(), 'mmm... more salt! yum :>').encode()
    
    def encrypt(self, content:str):
        global charNum
        global charList
        global charMap
        result = ""
        x = 0
        for char in content:
            if char == ' ':
                char = '_'
            if str(char) in charList:
                newchar = charList[(charMap[str(char)] + self.key[x % 64]) % charNum]
                result += newchar
            else:
                result += str(char)
            x += 1
        return result
    
    def decrypt(self, content:str):
        global charNum
        global charList
        global charMap
        result = ""
        x = 0
        for char in content:
            if str(char) in charList:
                newchar = charList[(charMap[char] - self.key[x % 64]) % charNum]
                result += newchar
            else:
                result += str(char)
            x += 1
        return result
    
class EncryptionException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

#generates a encryption key from a string seed
def generateKey(seed:str):
    seed_bytes = str(seed).encode()  # Convert seed to bytes
    kdf = PBKDF2HMAC(
        algorithm = hashes.SHA256(),
        length = 32,
        salt = b"mmm... salty",
        iterations=5,
    )
    return base64.urlsafe_b64encode(kdf.derive(seed_bytes))

#generates a hash from a seed using sha256 algorithm
def sha256(seed:str, salt:str="")->str:
    return hashlib.sha256((salt+seed).encode()).hexdigest()

#generates a hash from a seed using md5 algorithm
def md5(seed:str, salt:str="")->str:
    return hashlib.md5((salt+seed).encode('utf-8')).hexdigest()

CHUNKSIZE = 1024*256
ENCRCHUNKSIZE = 349624

def numberOfChunks(path:str):
    size = os.path.getsize(path)
    if path.endswith('.thth'):
        return ceil(size / ENCRCHUNKSIZE)
    return ceil(size / CHUNKSIZE)

#improved modification function, not memory intensive but slower and storage intensive. supports all file sizes and provides progress
def modifyByChunk(filePath:str, key:bytes, destinationFolder:str = None, makeCopy:bool = False, label:tk.Label=None, progressBar:ttk.Progressbar=None, root:tk.Tk=None):
    currentFileEncryptionProgress = 0
    currentFileEncryptionTotal = numberOfChunks(filePath)
    isEncrypting = not filePath.endswith('.thth')
    oldFileName = filePath.split(sep='\\')[-1]
    #if destinationFolder is not set to anything, make it the original folder.
    if destinationFolder == None:
        destinationFolder = filePath.removesuffix('\\' + oldFileName)

    if isEncrypting:
        name = Fernet(key).encrypt(oldFileName.encode()).decode()
        newFileName = name + ".thth"
    else:
        newFileName = Fernet(key).decrypt(oldFileName.removesuffix(".thth").encode()).decode()

    #forming new destination path
    newFilePath = destinationFolder + "\\" + newFileName
    piece = 100 / currentFileEncryptionTotal

    #open both files, then start transferring data from old file to new file, encrypting data in the process
    with open(filePath, 'rb') as oldFile, open(newFilePath, 'ab') as newFile:
        while True:
            if isEncrypting:
                chunk = oldFile.read(CHUNKSIZE)
                if not chunk:
                    break
                else:
                    modified = Fernet(key).encrypt(chunk)
                    newFile.write(modified)
            else:
                chunk = oldFile.read(ENCRCHUNKSIZE)
                if not chunk:
                    break
                else:
                    modified = Fernet(key).decrypt(chunk)
                    newFile.write(modified)
            currentFileEncryptionProgress += 1
            encryptionPercentage = round(currentFileEncryptionProgress/currentFileEncryptionTotal * 100, 1)
            if label:
                label.config(text=f"{'Encrypting' if isEncrypting else 'Decrypting'} file: {oldFileName if isEncrypting else newFileName}\n{encryptionPercentage}%")
                root.update()
            if progressBar:
                progressBar['value'] += piece
                root.update()

    #now that all our data is in the new file, delete the old file.
    if not makeCopy:
        os.remove(filePath)
    return newFilePath

#transfer file data from the temporary file to the encrypted file.
def reEncryptSingleFile(tempFilePath:str, encryptedFilePath:str, key:bytes, label:tk.Label=None, progressBar:ttk.Progressbar=None, root:tk.Tk=None):
    currentFileEncryptionTotal = numberOfChunks(tempFilePath)
    piece = 100 / currentFileEncryptionTotal
    currentFileEncryptionProgress = 0
    with open(encryptedFilePath, 'w') as file:
        pass #empty the encrypted file first, so that we can properly append chunks of data to it.
    with open(tempFilePath, 'rb') as oldFile, open(encryptedFilePath, 'ab') as newFile:
        while True:
            chunk = oldFile.read(CHUNKSIZE)
            if not chunk:
                break
            else:
                modified = Fernet(key).encrypt(chunk)
                newFile.write(modified)
            currentFileEncryptionProgress += 1
            encryptionPercentage = round(currentFileEncryptionProgress/currentFileEncryptionTotal * 100, 1)
            if label:
                label.config(text=f"Re-encrypting file:\n{tempFilePath}\n{encryptionPercentage}%")
            if progressBar:
                progressBar['value'] += piece
            root.update()

#? EVERYTHING BELOW IS NOT USED ANYMORE /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

"""
#given a file path, and a key, encrypt the file. #? DOES NOT SUPPORT VERY LARGE FILES, REPLACED BY MODIFYBYCHUNK
def modifyFile(isEncrypting:bool, filePath:str, key:bytes):

    #!if decrypting... check if filepath ends with .thth, if not then do not modify.
    if not isEncrypting:
        if not filePath.endswith(".thth"):
            return EncryptionException('File is not decryptable by Thoth.')

    #read and encrypt the contents of the file
    with open(filePath, 'rb') as file:
        data = file.read()
    modified = None

    #encrypt the data
    if isEncrypting:
        try:
            modified = Fernet(key).encrypt(data)
        except Exception as e:
            return e
    else:
        try:
            modified = Fernet(key).decrypt(data)
        except Exception as e:
            return e
    
    #then write back to it.
    with open(filePath, 'wb') as encrypted_file:
        encrypted_file.write(modified)
    
    #modifiying file name
    oldFileName = filePath.split(sep='\\')[-1]
    newFileName = None
    if isEncrypting:
        #!if encrypting, add the .thth extension before renaming
        try:
            newFileName = Fernet(key).encrypt(oldFileName.encode()).decode() + ".thth"
        except Exception as e:
            return e
    else:
        #!if decrypting... remove the .thth extension first before reverting to original filename.
        newFileName = Fernet(key).decrypt(oldFileName.removesuffix(".thth").encode()).decode()
    newPath = filePath.replace(oldFileName, newFileName)

    #rename the file.
    try:
        os.rename(filePath, newPath)
    except Exception as e:
        return e
    return newPath

#decrypt a single file, place it into a directory on the computer temporarily, then run it. #?REPLACED BY MODIFYBYCHUNK
def decryptSingleFile(filePath:str, key:bytes):

    #check if filepath ends with .thth, anything that doesn't will not be decrypted.
    if not filePath.endswith(".thth"):
        return Exception('Not decryptable by Thoth')
    
    #delete any existing temporary files first.
    for file in os.listdir(os.path.expanduser("~")+f"\AppData\Local\Thoth"):
        fullPath = os.path.expanduser("~")+f"\AppData\Local\Thoth\{file}"
        if file != 'data.ththscrpt' and os.path.isfile(fullPath):
            os.remove(fullPath)

    #get actual file name, create a temporary path
    encrName = filePath.split(sep='\\')[-1]
    actualName = Fernet(key).decrypt(encrName.removesuffix(".thth").encode()).decode()
    tempPath = os.path.expanduser("~")+f"\AppData\Local\Thoth\{actualName}"
    
    #read and decrypt the contents of the file
    with open(filePath, 'rb') as file:
        data = file.read()
    modified = None
    try:
        modified = Fernet(key).decrypt(data)
    except Exception as e:
        return e
    
    #write the contents to a file into the temporary path
    with open(tempPath, 'wb') as encrypted_file:
        encrypted_file.write(modified)
    
    #run the file.
    os.system(f'start "" "{tempPath}"')
    return tempPath

#only to be run if data is saved. #?REDESIGNED FUNCTION
def reEncryptSingleFile(tempPath:str, resultPath:str, key:bytes):
    with open(tempPath, 'rb') as file:
        data = file.read() #data contains bytes data of the 
    modified = None 
    try:
        modified = Fernet(key).encrypt(data)
    except Exception as e:
        return e
    with open(resultPath, 'wb') as encrypted_file:
        encrypted_file.write(modified)
"""