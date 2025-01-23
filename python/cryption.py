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
from tkinter import messagebox
from math import ceil
from itertools import cycle
import numpy as np
from xor_cipher import cyclic_xor

globalCurrentFileBeingModified = ""

USEXOR = True
CHUNKSIZE = 1024*256
ENCRCHUNKSIZE = 349624

class AES_Error(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class Cipher:
    def __init__(self, key: bytes):
        self.key = key
        if USEXOR:
            self.key_np = np.frombuffer(key, dtype=np.uint8)  # Convert key to NumPy array for XOR

    def encrypt(self, message: bytes) -> bytes:
        return Fernet(self.key).encrypt(message)

    def decrypt(self, cipherText: bytes) -> bytes:
        try:
            return Fernet(self.key).decrypt(cipherText)
        except:
            print("INVALID TOKEN / WRONG SIGNATURE")
            raise ValueError("MODIFIED CIPHER")
    
    def encrypt_XOR(self, message: bytes) -> bytes:
        return cyclic_xor(message, self.key)

    def decrypt_XOR(self, cipherText: bytes) -> bytes:
        return self.encrypt_XOR(cipherText)

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

def numberOfChunks(path:str):
    size = os.path.getsize(path)
    if path.endswith('.thth'):
        return ceil(size / ENCRCHUNKSIZE)
    return ceil(size / CHUNKSIZE)

#improved modification function, not memory intensive but slower and storage intensive. supports all file sizes and provides progress
#!THIS MBC FUNCTION IS NOT USED TO MODIFY FILES FOR ENCRYPTION, ONLY FOR MINOR FUNCTIONS ON CRYPTION.PY
def oldModifyByChunk(filePath:str, key:bytes, useXOR:bool, destinationFolder:str = None, makeCopy:bool = False, label:tk.Label=None, progressBar:ttk.Progressbar=None, root:tk.Tk=None):
    currentFileEncryptionProgress = 0
    currentFileEncryptionTotal = numberOfChunks(filePath)
    isEncrypting = not filePath.endswith('.thth')
    oldFileName = filePath.split(sep='\\')[-1]

    print(f"Now {'Encrypting' if isEncrypting else 'Decrypting'} {oldFileName} using {'XOR' if useXOR else 'AES'}!!!!!!!!!!!!!!!")
    #if destinationFolder is not set to anything, make it the original folder.
    if destinationFolder == None:
        destinationFolder = filePath.removesuffix('\\' + oldFileName)

    if isEncrypting:
        name = Cipher(key).encrypt(oldFileName.encode()).decode()
        newFileName = name + ".thth"
    else:
        newFileName = Cipher(key).decrypt(oldFileName.removesuffix(".thth").encode()).decode()

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
                    if useXOR:
                        modified = Cipher(key).encrypt_XOR(chunk)
                    else:
                        modified = Cipher(key).encrypt(chunk)
                    newFile.write(modified)
            else:
                chunk = oldFile.read(CHUNKSIZE if useXOR else ENCRCHUNKSIZE)
                if not chunk:
                    break
                else:
                    if useXOR:
                        modified = Cipher(key).encrypt_XOR(chunk)
                    else:
                        modified = Cipher(key).decrypt(chunk)
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
                if USEXOR:
                    modified = Cipher(key).encrypt_XOR(chunk)
                else:
                    modified = Cipher(key).encrypt(chunk)
                newFile.write(modified)
            currentFileEncryptionProgress += 1
            encryptionPercentage = round(currentFileEncryptionProgress/currentFileEncryptionTotal * 100, 1)
            if label:
                label.config(text=f"Re-encrypting file:\n{tempFilePath}\n{encryptionPercentage}%")
            if progressBar:
                progressBar['value'] += piece
            root.update()