#script is for encryption and hash related functions

import saveload
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from hashlib import md5
import tkinter as tk

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

#generates a hash from a seed using md5 algorithm
def mdHash(seed:str)->str:
    return md5(seed.encode('utf-8')).hexdigest()

def numberOfChunks(folderPath:str, chunkSize:int=1024*64):
    size = os.path.getsize(folderPath)
    return size // chunkSize

#improved modification function, not memory intensive but slower and storage intensive.
def modifyByChunk(isEncrypting:bool, filePath:str, key:bytes, destinationFolder:str = None, chunkSize:int = 1024*64):
    #!if decrypting... check if filepath ends with .thth, if not then do not modify.
    if not isEncrypting:
        if not filePath.endswith(".thth"):
            return EncryptionException('File is not decryptable by Thoth.')
    
    #if destinationFolder is not set to anything, make it the original folder.
    if destinationFolder == None:
        destinationFolder = filePath.removesuffix('\\' + filePath.split(sep='\\')[-1])

    #modifiying file name
    oldFileName = filePath.split(sep='\\')[-1]
    if isEncrypting:
        #!if encrypting, add the .thth extension before renaming
        try:
            newFileName = Fernet(key).encrypt(oldFileName.encode()).decode() + ".thth"
        except Exception as e:
            return e
    else:
        #!if decrypting... remove the .thth extension first before reverting to original filename.
        newFileName = Fernet(key).decrypt(oldFileName.removesuffix(".thth").encode()).decode()

    #forming new destination path
    newFilePath = destinationFolder + "\\" + newFileName

    #open both files, then start transferring data from old file to new file, encrypting data in the process
    with open(filePath, 'rb') as oldFile:
        newFile = open(newFilePath, 'ab')
        while True:
            chunk = oldFile.read(chunkSize)
            if not chunk:
                break
            else:
                #modify one 4KB chunk of data
                if isEncrypting:
                    modified = Fernet(key).encrypt(chunk)
                else:
                    modified = Fernet(key).decrypt(chunk)
                #append modified file into the new file path.
                newFile.write(modified)
        newFile.close()

    #now that all our data is in the new file, delete the old file.
    os.remove(filePath)
    return newFilePath

#given a file path, and a key, encrypt the file.
#returns the new path if successful, and returns an exception if unsuccessful
#function makes use of .thth file extension to check whether or not a file has been encrypted by Thoth.
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

#decrypt a single file, place it into a directory on the computer temporarily, then run it.
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

def compareFileContents(path1:str, path2:str)->bool:
    return open(path1, 'rb').read() == open(path2, 'rb').read()

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

inp = input('enter a file path: ')
print(numberOfChunks(inp), '64KB chunks')
print(os.path.getsize(inp))
path = modifyByChunk(isEncrypting=True, filePath=inp, key=generateKey('dimas'))
print(os.path.getsize(path))