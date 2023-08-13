#script is for encryption and hash related functions

import saveload
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import hashlib
import tkinter as tk
from math import ceil

globalCurrentFileBeingModified = ""

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
def sha256(seed:str)->str:
    return hashlib.sha256(seed.encode()).hexdigest()

#generates a hash from a seed using md5 algorithm
def mdHash(seed:str)->str:
    return hashlib.md5(seed.encode('utf-8')).hexdigest()

CHUNKSIZE = 1024*256

def numberOfChunks(path:str, chunkSize:int = CHUNKSIZE):
    size = os.path.getsize(path)
    return ceil(size / chunkSize)

globalCurrentEncryptionPercentage = 0

#improved modification function, not memory intensive but slower and storage intensive. supports all file sizes and provides progress
def modifyByChunk(filePath:str, key:bytes, destinationFolder:str = None, chunkSize:int = CHUNKSIZE, makeCopy:bool = False):
    global globalCurrentEncryptionPercentage
    globalCurrentEncryptionPercentage = 0
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

    #open both files, then start transferring data from old file to new file, encrypting data in the process
    with open(filePath, 'rb') as oldFile, open(newFilePath, 'ab') as newFile:
        print(f'currently modifying {filePath}')
        while True:
            if isEncrypting:
                chunk = oldFile.read(chunkSize) 
                if not chunk:
                    break
                else:
                    modified = Fernet(key).encrypt(chunk)
                    newFile.write(modified)
            else:
                chunk = oldFile.read(349624)
                if not chunk:
                    break
                else:
                    modified = Fernet(key).decrypt(chunk)
                    newFile.write(modified)
            currentFileEncryptionProgress += 1
            globalCurrentEncryptionPercentage = round(currentFileEncryptionProgress/currentFileEncryptionTotal * 100, 1)
            print(f'modification progress: {globalCurrentEncryptionPercentage}%')

    #now that all our data is in the new file, delete the old file.
    if not makeCopy:
        os.remove(filePath)
    return newFilePath

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

#only to be run if data is saved. #?REPLACED BY MODIFYBYCHUNK
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