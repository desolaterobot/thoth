#script is for encryption and hash related functions

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from hashlib import md5

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

#given a file path, and a key, encrypt the file.
#returns the new path if successful, and returns an exception if unsuccessful
#function makes use of .thth file extension to check whether or not a file has been encrypted by Thoth.
def modifyFile(isEncrypting:bool, filePath:str, key:bytes):
    #!if decrypting... check if filepath ends with .thth, if not then do not modify.
    if not isEncrypting:
        if not filePath.endswith(".thth"):
            return Exception('Not decryptable by Thoth')
        
    #read and encrypt the contents of the file
    with open(filePath, 'rb') as file:
        data = file.read()
    modified = None
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
        except:
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