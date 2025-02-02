#main script: renders window and GUI functions

from fileclass import *
from PIL import Image, ImageTk
from tkinter import ttk
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import PhotoImage
import cryptography.fernet
from filehashing import hash_files
import time
import string
import random
import shortcuts
import drive
from io import BytesIO
from icon import image_strg, ico_icon

# GLOBAL VARIABLES ######################################################################################

currentDirectorySize = 0
prevTimeString = ""
numberOfChunks = 0
chunkTime1 = 0
chunkTime2 = 0
globalVersionNumber = '1.5'
globalTitlePathDict = dict()
globalCurrentlySelectedPath:str = None
globalCurrentDirectoryObject:Directory = None
globalIsTranslatedBoolean = False
globalWrongTries = saveload.getData('wrongTries', 0)
thothDirectory = os.path.dirname(os.path.abspath(__file__)).removesuffix("\\python")

MAXFILENAMELENGTH = 200

# FUNCTIONS #############################################################################################

#takes an int time in seconds, then converts into a string that shows the hours, minutes and seconds.
def intToTimeString(seconds):
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return f"{f'{round(hours)} hours ' if hours>0 else ''}{f'{round(minutes)} minutes ' if minutes>0 else ''}{round(seconds, 2)} seconds"

#includes the 'wrong passcode' message window if passcode is false.
def checkPass():
    #!check if the given key is correct by checking if the md5 hash of the given key matches the hash in thoth script.
    givenHash = globalCurrentDirectoryObject.encryptionHash
    key = generateKey(passBox.get())
    hashKey = sha256(key.decode())
    if hashKey != givenHash:
        global globalWrongTries
        globalWrongTries += 1
        saveload.setData('wrongTries', globalWrongTries)
        messagebox.showerror('Wrong passcode', f'The passcode entered does not match the passcode used for the encryption of this folder. {globalWrongTries} wrong attempts so far.')
        return False
    return True

#if folder is encrypted, check for password, then translate all the encrypted filenames in the listbox.
def translateListBox():
    if not globalCurrentDirectoryObject.isEncrypted:
        return
    newTitles = []
    newDict = {}
    global globalTitlePathDict
    global globalIsTranslatedBoolean
    if not globalIsTranslatedBoolean:
        if not checkPass():
            return
        for title,path in globalTitlePathDict.items():
            if isFile(path):
                encryptedFileName = os.path.splitext(path)[0].split(sep='\\')[-1]
                try:
                    decryptedFileName = Cipher(generateKey(passBox.get())).decrypt(encryptedFileName.encode()).decode() #contains the original extension
                except:
                    messagebox.showerror('Folder contains some unencrypted files.', 'We can only translate FULLY encrypted folders. Look into the folder that contains unencrypted files and encrypt them first.')
                    return
                newTitle = title.replace(encryptedFileName + ".thth", decryptedFileName)
                newTitles.append(newTitle)
                newDict[newTitle] = path
            else:
                newTitles.append(title)
                newDict[title] = path
        dirlistbox.config(fg=purpleTextColor)
        removeFileButton.config(state='disabled')
        renameButton.config(state='disabled')
        globalTitlePathDict = newDict
        #showing the listbox with updated titles.
        showListBox(dirlistbox, newTitles)
        statusLabel2.config(text="Translated encrypted names into their original names.", fg=purpleTextColor)
        globalIsTranslatedBoolean = not globalIsTranslatedBoolean
    else:
        dirlistbox.config(fg=blueTextColor)
        refreshListBox(None, globalCurrentDirectoryObject.path)

def centerWindow(window, width, height):
    # Get the screen width and height
    screenW = window.winfo_screenwidth()
    screenH = window.winfo_screenheight()
    x = (screenW // 2) - (width // 2)
    y = (screenH // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    try:
        window.iconbitmap(joinAddr(thothDirectory, "\\assets\\icon.ico"))
        #image = tk.PhotoImage(data=base64.b64decode(ico_icon))
        #root.iconphoto(True, image)
    except:
        pass

def showRightFrame(isNormal):
    rightFrame.grid(column=2, row=0, sticky=tk.N+tk.S+tk.E+tk.W)
    if isNormal:
        encrButtonFrame.pack_forget()
        normalButtonFrame.pack()
    else:
        normalButtonFrame.pack_forget()
        encrButtonFrame.pack()

def hideRightFrame():
    rightFrame.grid_forget()

def showListBox(listbox:tk.Listbox, items:list):
    listbox.delete(0, 'end')
    for item in items:
        listbox.insert(tk.END, item)

def appendListBox(listbox:tk.Listbox, item: str):
    listbox.insert(tk.END, item)

def disableWidgets(widgetTuple:tuple):
    for widget in widgetTuple:
        widget.config(state='disabled')

def enableWidgets(widgetTuple:tuple):
    for widget in widgetTuple:
        widget.config(state='normal')

def progressWindow(title:str='', labelText:str='', size:tuple=(500,125)):
    window = tk.Toplevel(root)
    centerWindow(window, size[0], size[1])
    window.title(title)
    textBox = tk.Label(window, text=labelText, font=('Microsoft Sans Serif', 12))
    textBox.pack(padx=5, pady=(5, 5))
    progressBar = ttk.Progressbar(window, orient='horizontal', length=300, mode='determinate')
    progressBar.pack(padx=5, pady=(8, 8))
    return window, textBox, progressBar

def topWindow(title:str='', labelText:str='', size:tuple=(500,150)):
    window = tk.Toplevel(root)
    centerWindow(window, size[0], size[1])
    window.title(title)
    textBox = tk.Label(window, text=labelText, font=('Microsoft Sans Serif', 12))
    textBox.pack(padx=5, pady=(5, 5))
    return window, textBox

# function is RECURSIVE! 
def showDirectory(e, directory:str, nestvalue:int=0):
    global globalCurrentDirectoryObject
    targetDirectory = path2Dir(directory)
    fileCount = 0
    dirCount = 0
    global globalTotalFilesFound
    for item in targetDirectory.contents:
        statusLabel2.config(text=f'{item.name} listed.')
        if isinstance(item, File):
            globalTotalFilesFound += 1
            fileCount += 1
            title = f"{nestvalue * '    '}FILE {fileCount}/{targetDirectory.totalFileCount}: {item.name} - {sizeToString(item.getSize())}"
            appendListBox(dirlistbox, title)
            globalTitlePathDict[title] = item.path
        elif isinstance(item, Directory):
            dirCount += 1
            title = f"{nestvalue * '    '}FOLDER {dirCount}/{targetDirectory.totalDirCount}: {item.name} {('(' + item.encryptionMethod + ')') if item.encryptionMethod else ''} - contains {item.totalFileCount} files, {item.totalDirCount} folders:" 
            appendListBox(dirlistbox, title)
            globalTitlePathDict[title] = item.path
            showDirectory(None, item.path, nestvalue + 1)
        statusLabel.config(text=f'Showing target folder... {globalTotalFilesFound} files listed so far.')
        root.update()
    globalCurrentDirectoryObject = targetDirectory
    return targetDirectory

def showStatus(directory):
    #display status of target file on the label text at the bottom
    def changeStatusLabel(directory:Directory):
        size = sizeToString(directory.getSize())
        name = directory.name
        dircount = directory.totalDirCount
        filecount = directory.totalFileCount
        completefilecount = directory.getCompleteFileCount()
        statusLabel.config(text=f'{name} has {filecount} files, {dircount} subfolders. Including subfolders, {completefilecount} files with total size {size}')
        showRightFrame(not directory.isEncrypted)

    global globalTotalFilesFound
    globalTotalFilesFound = 0
    global globalIsTranslatedBoolean
    globalIsTranslatedBoolean = False
    dirBox.delete(0, tk.END)
    dirBox.insert(0, directory)
    saveload.setData("lastVisited", directory)
    disableWidgets((dirBox, lookInFolderButton, renameButton, deleteFileButton, findDirectoryButton, refreshButton, settingsButton, openFolderButton, parentFolderButton, translateFolderButton, decryptFolderButton))
    startTime = time.time()
    statusLabel.config(text=f'Searching target folder... you seem to have a lot of files here...')
    root.update()
    changeStatusLabel(showDirectory(None, directory))
    endTime = time.time()
    enableWidgets((dirBox, findDirectoryButton, refreshButton, settingsButton, openFolderButton, parentFolderButton, translateFolderButton, decryptFolderButton))
    #apparently '.3g' is the 3sf specifier????
    statusLabel2.config(text=f'Time taken to walk through {directory}: {(endTime-startTime):.3g} seconds.', fg='white')
    #change listbox color based on if file is encrypted or not.
    if globalCurrentDirectoryObject.isEncrypted: #this is going on r/programminghorror for sure
        dirlistbox.config(bg=encrListCol, fg=blueTextColor, selectbackground=blueTextColor, selectforeground=encrListCol)
        leftFrame.config(bg=encrBGCol)
        rightFrame.config(bg=encrSideCol)
        statusLabel.config(bg=encrBGCol)
        statusLabel2.config(bg=encrBGCol)
        targetLabel.config(bg=encrBGCol)
        passcodeLabel.config(bg=encrBGCol)
        buttonLF.config(bg=encrBGCol)
    else:
        dirlistbox.config(bg=normalListCol, fg=greenTextColor, selectbackground=greenTextColor, selectforeground=normalListCol)
        leftFrame.config(bg=normalBGCol)
        rightFrame.config(bg=normalSideCol)
        statusLabel.config(bg=normalBGCol)
        statusLabel2.config(bg=normalBGCol)
        targetLabel.config(bg=normalBGCol)
        passcodeLabel.config(bg=normalBGCol)
        buttonLF.config(bg=normalBGCol)
    return

#show the selected directory again, referring to the textbox instead of the directory finder
def refreshListBox(e, directory:str):
    if directory == "":
        hideRightFrame()
        return
    globalTitlePathDict.clear()
    showListBox(dirlistbox, [])
    #check if directory is empty
    #check if given directory exists
    if not os.path.exists(directory):
        hideRightFrame()
        print(f"{directory} does not exist. Type another directory.")
        messagebox.showerror(title='Does not exist', message=f'Folder "{directory}" does not exist. Did you type it correctly?')
        return
    showStatus(directory)

#open the directory finder and show the selected directory onto the list box
def searchDirectory():
    globalTitlePathDict.clear()
    filepath = filedialog.askdirectory(title='Select target directory...')
    #another warning hereeee
    if filepath.endswith(':') or filepath == os.path.expanduser("~") or len(filepath.split('\\')) == 2:
        if not messagebox.askyesno(f"Dangerous folder", f"Thoth does not reccommend encrypting or even looking into {filepath} due to its size and importance. Look into it anyway?"):
            return
    if filepath == '':
        return
    hideRightFrame()
    showListBox(dirlistbox, [])
    filepath = filepath.replace('/', '\\')
    showStatus(filepath)

#delete currently selected path/file
def deleteSelectedFile():
    if messagebox.askyesno(title='Confirm deletion', message=f'Are you sure you want to permanently delete {globalCurrentlySelectedPath}?'):
        from shutil import rmtree
        if isFile(globalCurrentlySelectedPath):
            os.remove(globalCurrentlySelectedPath)
        else:
            try:
                rmtree(globalCurrentlySelectedPath)
            except PermissionError:
                messagebox.showerror(title='Permission error', message=f'Unable to access {globalCurrentlySelectedPath}')
        refreshListBox(None, globalCurrentDirectoryObject.path)

#changing of target directory to the currently selected path
def lookInFolder():
    dirBox.delete(0, tk.END)
    dirBox.insert(0, globalCurrentlySelectedPath)
    refreshListBox(None, globalCurrentlySelectedPath)

#! JUST MOVED OUTSIDE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def modifyByChunk(
        filePath:str, 
        key:bytes,

        textBox:ttk.Label = None, # Label object for the label at the bottom of the window.
        progressBar:ttk.Progressbar = None, # Progressbar to be updated every iteration of chunk encryption
        piece:float = None, # Piece of progressbar to be added every successful chunk encryption
        encryptionProgress:int = None, # current value of encryption progress to be displayed in the window,
        totalFileNum:int = None, # Total files in directory
        makeCopy:bool = False,
        destinationFolder:str = None,
        chunkSize:int = CHUNKSIZE
    ):
    
    #recording how much time is taken for a certain number of chunks is encrypted.
    def checkChunks(sample):
        global chunkTime1
        global chunkTime2
        global numberOfChunks
        #print(chunkTime1, chunkTime2, numberOfChunks)
        if numberOfChunks == 0:
            chunkTime1 = time.time()
        elif numberOfChunks >= sample:
            numberOfChunks = -1
            chunkTime2 = time.time()
            timeTakenFor5Chunks = chunkTime2 - chunkTime1 
            global currentDirectorySize
            totalTimeTaken = (timeTakenFor5Chunks/(sample*256*1024))*(currentDirectorySize)
            return intToTimeString(totalTimeTaken)
        return ""

    #print(f'start modification function {filePath}')
    currentFileEncryptionProgress = 0
    #currentFileEncryptionTotal = numberOfChunks(filePath)
    isEncrypting = not filePath.endswith('.thth')
    oldFileName = filePath.split(sep='\\')[-1]
    #if destinationFolder is not set to anything, make it the original folder.
    if destinationFolder == None:
        destinationFolder = filePath.removesuffix('\\' + oldFileName)
    cipher = Cipher(key)
    if isEncrypting:
        name = cipher.encrypt(oldFileName.encode()).decode()
        newFileName = name + ".thth"
        if len(newFileName) > MAXFILENAMELENGTH:
            #if the filename is too long, rename the file.
            currentFolder = filePath.removesuffix('\\' + oldFileName)
            renamedFile = md5(os.path.splitext(oldFileName)[0]) + os.path.splitext(oldFileName)[1]
            os.rename(currentFolder + '\\' + oldFileName, currentFolder + '\\' + renamedFile)
            oldFileName = renamedFile
            newFileName = cipher.encrypt(oldFileName.encode()).decode() + ".thth"
            filePath = currentFolder + '\\' + renamedFile
    else:
        if oldFileName.endswith(".thth"):
            newFileName = cipher.decrypt(oldFileName.removesuffix(".thth").encode()).decode()
        else:
            print(f"error decrypting {filePath}")

    #forming new destination path
    newFilePath = destinationFolder + "\\" + newFileName

    #open both files, then start transferring data from old file to new file, encrypting/decrypting data in the process

    with open(filePath, 'rb') as oldFile, open(newFilePath, 'ab') as newFile:
        while True:
            if isEncrypting:
                chunk = oldFile.read(chunkSize) 
                if not chunk:
                    break
                else:
                    if USEXOR:
                        modified = cipher.encrypt_XOR(chunk)
                    else:
                        modified = cipher.encrypt(chunk)
                    newFile.write(modified)
            else:
                chunk = oldFile.read(chunkSize if USEXOR else 349624)
                if not chunk:
                    break
                else:
                    if USEXOR:
                        modified = cipher.encrypt_XOR(chunk) #XOR encryption is symmetric
                    else:
                        try:
                            modified = cipher.decrypt(chunk)
                        except:
                            raise AES_Error(newFilePath)
                    newFile.write(modified)
            currentFileEncryptionProgress += 1
            global currentDirectorySize
            if isEncrypting:
                currentDirectorySize -= CHUNKSIZE
            else:
                currentDirectorySize -= ENCRCHUNKSIZE
            #globalCurrentEncryptionPercentage = round(currentFileEncryptionProgress/currentFileEncryptionTotal * 100, 1)
            global numberOfChunks
            global prevTimeString
            timeString = checkChunks(100)
            if timeString != "":
                prevTimeString = timeString
            message = f"{'Encrypting' if isEncrypting else 'Decrypting'} file: {oldFileName if isEncrypting else newFileName}\nSize: {sizeToString(os.path.getsize(filePath))} Progress: {round(progressBar['value'], 3)}%\n{encryptionProgress}/{totalFileNum} Files Processed\nEstimated time taken: {prevTimeString}"
            numberOfChunks += 1
            if textBox:
                textBox.config(text=message)
            progressBar['value'] += piece
            root.update()
            
    #now that all our data is in the new file, delete the old file.
    if not makeCopy:
        try:
            os.remove(filePath)
        except:
            messagebox.showwarning(title="Unable to remove file.", message=f"Permission denied error: unable to remove file: {filePath}")
            pass
    return newFilePath

#binded to the button that says "Encrypt folder"
#the folder encryption function here is non-recursive, unlike the object method modifyDirectory()
def startModification(isEncrypting:bool):
    global globalCurrentDirectoryObject
    global USEXOR

    def start():
        global globalCurrentDirectoryObject
        modWindow.title(f"{'Encrypting' if isEncrypting else 'Decrypting'} files... DO NOT CLOSE UNTIL COMPLETION.")
        encryptButton.pack_forget()
        encryptXORButton.pack_forget()
        textBox.config(text='\nModification cannot start for some reason. Refresh and try again.')
        #encryption steps: modification, update current directory, update the list box.
        key = generateKey(passBox.get())
        currentDirectory = globalCurrentDirectoryObject.path

        #*BEFORE FOLDER MODIFICATION, MAKE SOME CHECKS////////////////////////////////////////////////////////////////////////////////////////////////
        
        #get list of folders and subfolders.
        folderList = globalCurrentDirectoryObject.getCompleteFolderPathList()
        thisPath = globalCurrentDirectoryObject.path
        folderList.append(thisPath)
        totalFileNum = len(fileList)
        encryptionProgress = 0
        chunkNumberFolder = 0
        for file in globalCurrentDirectoryObject.getCompleteFilePathList():
            chunkNumberFolder += ceil(os.path.getsize(file) / (CHUNKSIZE if isEncrypting else (349624 if not USEXOR else CHUNKSIZE)))
        piece = (100/chunkNumberFolder)
        progressBar = ttk.Progressbar(modWindow, orient='horizontal', length=460, mode='determinate')
        progressBar.pack(padx=5, pady=(8, 8))
        
        disableWidgets((dirlistbox, dirBox, lookInFolderButton, renameButton, deleteFileButton, findDirectoryButton, refreshButton, settingsButton, openFolderButton, parentFolderButton, translateFolderButton, decryptFolderButton, encryptFolderButton, addFilesButton, removeFileButton))
        global currentDirectorySize
        currentDirectorySize = globalCurrentDirectoryObject.getSize()

        if isEncrypting:
            #!before encryption... we save the data into a .ththscrpt file in each subfolder, to signify an encryption by Thoth
            #!This is done just in case encryption fails
            thothInfo = {
                "method" : "XOR" if USEXOR else "AES",
                "hash" : sha256(key.decode())
            }
            for folderPath in folderList:
                textBox.config(text=f"Placing folder data...\n{folderPath}")
                name = folderPath.split(sep='\\')[-1]
                open(joinAddr(folderPath, f"{name}.ththscrpt"), "w").write(str(thothInfo))
                progressBar['value'] += piece
                root.update()

        startTime = time.time() #*START OF MODIFICATION PROCESS ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////``
        failures = []
        
        for filePath in fileList:
            try:
                modifyByChunk(filePath, key, textBox, progressBar, piece, encryptionProgress, totalFileNum)
            except AES_Error as ex:
                newFullPath = ex.message
                newFileName = os.path.split(newFullPath)[-1]
                print("ORIGINAL FILENAME: " + newFileName)
                failures.append(newFullPath)
            encryptionProgress += 1
            root.update()

        # take care of any failures
        if len(failures) > 0:
            for failure in failures:
                os.remove(failure)
            messagebox.showerror("MODIFIED CIPHERTEXT!", f"The ciphertext for {str([os.path.split(failure)[-1] for failure in failures])} may have been modified somehow, making it impossible to decrypt. Please find a backup of these files somewhere else. The corrupted encrypted file will be left in this folder, for you to remove as you please.")
            
        global prevTimeString
        prevTimeString = ""
        endTime = time.time() #*END OF MODIFICATION PROCESS //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        
        progressBar['value'] = 0
        root.update()
        piece = (100 / len(folderList))

        if not isEncrypting:
            #!after decryption... we remove the .ththscrpt file entirely in each subfolder, to show that the folder is normal.
            for folderPath in folderList:
                textBox.config(text=f"Removing folder data...\n{folderPath}")
                name = folderPath.split(sep='\\')[-1]
                folderScriptPath = joinAddr(folderPath, f"{name}.ththscrpt")
                if sha256(key.decode()) == eval(open(folderScriptPath, 'r').read())['hash']:
                    #the hash inside this script matches the hash of the passcode given.
                    os.remove(folderScriptPath)
                progressBar['value'] += piece
                root.update()

        textBox.config(text=f"Refreshing...")
        progressBar.pack_forget()
        root.update()
        globalCurrentDirectoryObject = path2Dir(currentDirectory) #updating current directory
        enableWidgets((dirlistbox, dirBox, findDirectoryButton, refreshButton, settingsButton, openFolderButton, parentFolderButton, translateFolderButton, decryptFolderButton, encryptFolderButton, addFilesButton))
        refreshListBox(None, currentDirectory) #update listbox
        statusLabel2.config(text=f"{'Encrypted' if isEncrypting else 'Decrypted'} target directory in {intToTimeString(endTime-startTime)}. {len(failures)} failures.", fg='white')
        modWindow.destroy()
    
    def AESstart():
        global USEXOR
        if isEncrypting:
            USEXOR = False
        else:
            USEXOR = True if globalCurrentDirectoryObject.encryptionMethod == 'XOR' else False
        start()

    def XORstart():
        global USEXOR
        USEXOR = True
        start()
    
    #check if the folder is COMPLETELY encrypted or unencrypted.
    #getting the complete list of filepaths.
    try:
        fileList = globalCurrentDirectoryObject.getCompleteFilePathList()
    except:
        #error getting list
        showDirectory(None, dirBox.get())
        start()

    for file in fileList:
        folder = file.removesuffix('\\' + file.split(sep='\\')[-1])
        if globalCurrentDirectoryObject.isEncrypted:
            if not file.endswith('.thth'):
                messagebox.showerror('Folder is not fully encrypted.', f'Unencrypted files are found at {folder}. Please look into this folder and delete or encrypt these files first.')
                return
        else:
            if file.endswith('.thth'):
                messagebox.showerror('Folder is not fully decrypted.', f'Encrypted files are found at {folder}. Please look into this folder and delete or decrypt these files first.')
                return

    if passBox.get() == "":
        messagebox.showerror(title='No passcode entered', message=f"Please enter a passcode before you {'encrypt' if isEncrypting else 'decrypt'}.")
        return 
    if not isEncrypting:
        if not checkPass():
            return
        
    #modification window
    if isEncrypting:
        newSize = globalCurrentDirectoryObject.getSize()*1.33333
        change = f"Estimated AES size increase: {sizeToString(globalCurrentDirectoryObject.getSize())} -> {sizeToString(newSize)}"
    else:
        newSize = globalCurrentDirectoryObject.getSize()*0.75
        change = f"Estimated AES size decrease: {sizeToString(globalCurrentDirectoryObject.getSize())} -> {sizeToString(newSize)}"
    sizeChange = newSize - globalCurrentDirectoryObject.getSize()

    # drive space checking function is not tested at all btw
    if sizeChange > 0:
        if sizeChange*1.1 > drive.driveCapacity(globalCurrentDirectoryObject.path)['free']:
            messagebox.showerror("Insufficient space.", f"More space required for encryption. {change}")
            return

    modWindow = tk.Toplevel(root)
    centerWindow(modWindow, 500, 180)
    modWindow.title(f"Confirm {'Encryption' if isEncrypting else 'Decryption'}")
    textFrame = tk.Frame(modWindow, width=500, height=90);
    textBox = tk.Label(textFrame, text=f"You are about to {'encrypt' if isEncrypting else 'decrypt'}\nthe target folder with the given passcode. Proceed?\n{change}", font=('Microsoft Sans Serif', 12), justify="left")
    textBox.pack(side='left')
    textFrame.pack(padx=15, pady=(5, 0))
    textFrame.pack_propagate(False)
    encryptButton = tk.Button(modWindow, text=f"Start {'Encryption' if isEncrypting else 'Decryption'} with {'XOR' if globalCurrentDirectoryObject.encryptionMethod == 'XOR' else 'AES'}", font=('Arial', 13), command=AESstart)
    encryptButton.pack(padx=5, pady=(0, 2))
    encryptXORButton = tk.Button(modWindow, text=f"Start Encryption with XOR", font=('Arial', 13), command=XORstart)
    
    #!newly added
    if isEncrypting:
        encryptXORButton.pack(padx=5, pady=(5, 2))
    
    encryptButton.focus()

#such a tedious function for something that is not really related to encryption
def renameCurrentFile():
    def onSubmit(e=None):
        #renaming
        newName = nameEntry.get()
        if newName == "":
            messagebox.showerror("Name not entered", "You cannot have a blank filename wtf")
            return
        newNameAndExtension = newName + extension
        newName2 = newNameAndExtension
        if globalIsTranslatedBoolean: #! before renaming the encrypted file, we must first encrypt the new name.
            newNameAndExtension = Cipher(encryptionKey).encrypt(newNameAndExtension.encode()).decode() + '.thth'
        newPath = globalCurrentlySelectedPath.replace(name, newNameAndExtension)
        renameWindow.destroy()
        os.rename(globalCurrentlySelectedPath, newPath) #renaming the file itself.
        #changing the listbox content
        selected = dirlistbox.curselection()
        if not selected:
            print('unselected.')
            return
        itemSelected:str = dirlistbox.get(selected[0])
        if globalIsTranslatedBoolean: #! before changing the listbox content, if we are in translated mode, translate the file first before changing.
            newText = itemSelected.replace(Cipher(encryptionKey).decrypt(name.removesuffix('.thth').encode()).decode(), newName2)
        else:
            newText = itemSelected.replace(name, newNameAndExtension)
        dirlistbox.delete(selected[0])
        dirlistbox.insert(selected[0], newText)
        #change the key-value pair in the globalDictionary
        globalTitlePathDict[newText] = globalTitlePathDict.pop(itemSelected)
        globalTitlePathDict[newText] = newPath
        print('renamed.')
    global globalCurrentlySelectedPath
    global globalIsTranslatedBoolean
    if globalIsTranslatedBoolean:
        if not checkPass():
            return
    encryptionKey = generateKey(passBox.get())
    #getting the file extension
    name = globalCurrentlySelectedPath.split('\\')[-1] #gets the pure filename
    if name.endswith('.thth') and not globalIsTranslatedBoolean:
        messagebox.showerror('Attempting to rename encrypted file', 'Cannot rename file in non-translated mode. Click on "Translate" then try again.')
        return
    extension = os.path.splitext(name)[1] #gets the file extension from the pure filename
    if globalIsTranslatedBoolean: #! if file is encrypted, to get the extension, remove the .thth suffix first, decrypt the name, then get extension.
        extension = os.path.splitext(Cipher(encryptionKey).decrypt(name.removesuffix('.thth').encode()).decode())[1] #getting the extension if name is encrypted
    #creating the toplevel window
    renameWindow = tk.Toplevel(root)
    centerWindow(renameWindow, 300, 120)
    renameWindow.title("Rename file/folder")
    label = tk.Label(renameWindow, text=f"Enter the new name for {name if not globalIsTranslatedBoolean else Cipher(encryptionKey).decrypt(name.removesuffix('.thth').encode()).decode()}.\nFile extension added automatically.")
    label.pack(pady=5, padx=10)
    nameEntry = tk.Entry(renameWindow, width=40, bg='#bababa')
    nameEntry.pack(pady=5, padx=10)
    nameEntry.focus_set()
    nameEntry.bind()
    nameEntry.bind("<Return>", onSubmit)
    okButton = tk.Button(renameWindow, text='Rename', font=('Arial', 10), command=onSubmit)
    okButton.pack(pady=5)

def openFileExplorer():
    if not globalCurrentDirectoryObject == None:
        os.system(f'start "" "{globalCurrentDirectoryObject.path}"')

def openSettings():
    def saveSettings():
        extensions = extensionsBox.get().strip(', ').split(sep=',')
        for e in extensions:
            if not e.startswith('.'):
                messagebox.showerror('Invalid file extension',f'{e} is not a valid file extension.')
                return
        extensions.append('.ththscrpt')
        extensions = list(set(extensions))
        saveload.setData('forbidden', extensions)
        settingsWindow.destroy()
    
    def generatePasscode():
        passc = ""
        completeCharList = string.ascii_letters + string.digits + string.punctuation
        charListLen = len(completeCharList)
        for x in range(32):
            passc += completeCharList[random.randint(0, charListLen-1)]
        passGenBox.delete(0, tk.END)
        passGenBox.insert(0, passc)
    
    def saveToDesktop(num=1):
        password = passGenBox.get()
        if not password:
            messagebox.showerror('No passcode generated', "No passcode generated, nothing is saved. Click on 'Generate And Enter' first.")
            settingsWindow.destroy()
            return
        if globalCurrentDirectoryObject:
            addr = joinAddr(os.path.expanduser("~/Desktop"), f"{globalCurrentDirectoryObject.name}{num}.txt")
            name = globalCurrentDirectoryObject.name + f'{num}.txt'
        else:
            addr = joinAddr(os.path.expanduser("~/Desktop"), f"passcode{num}.txt")
            name = f'passcode{num}.txt'

        if not os.path.exists(addr):
            open(addr, 'w').write(password)
            messagebox.showinfo('Passcode saved!', f'Passcode saved on your desktop: {name}\nHide it before someone finds it!')
            settingsWindow.destroy()
        else:
            saveToDesktop(num+1)
    
    def putShortcutToDesktop():
        fullpath = os.path.abspath("thoth.exe")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcuts.createShortcut(fullpath, 'ThothCrypt', desktop)
        settingsWindow.destroy()
    
    def lastVisitedToggle():
        saveload.setData("enableLastVisited", enableLastVisited.get())
        if not enableLastVisited.get():
            saveload.setData("lastVisited", None)
        pass

    def autoRefreshToggle():
        saveload.setData("enableAutoRefresh", enableAutoRefresh.get())
        pass

    enableLastVisited = tk.BooleanVar(value=saveload.getData("enableLastVisited", False))
    enableAutoRefresh = tk.BooleanVar(value=saveload.getData("enableAutoRefresh", False))

    settingsWindow = tk.Toplevel()
    settingsWindow.title('ThothCrypt Settings')
    centerWindow(settingsWindow, 500, 650)
    settingsWindow.focus_force()
    settingsWindow.config(bg=normalSideCol)
    # image
    try:
        img = Image.open(BytesIO(base64.b64decode(image_strg))).resize((100,100))
        photo = ImageTk.PhotoImage(img)
        image_label = tk.Label(settingsWindow, image=photo, bg=normalSideCol)
        image_label.image = photo
        image_label.pack(pady=10)
    except:
        pass
    label0 = tk.Label(settingsWindow, text=f'ThothCrypt {globalVersionNumber}', font=('Microsoft Sans Serif', 13), bg=normalSideCol, fg=textColor)
    label0.pack()
    #forbidden file extensions
    label1 = tk.Label(settingsWindow, text='Forbidden file extensions', font=('Microsoft Sans Serif', 14), bg=normalSideCol, fg=textColor)
    label1.pack(pady=(10,0))
    label2 = tk.Label(settingsWindow, text='Thoth ignores all files that contains these extensions.\nType them as seperated by only commas.', font=('Microsoft Sans Serif', 10), bg=normalSideCol, fg=textColor)
    label2.pack(pady=(0,2))
    startingEntry = ""
    for item in saveload.getData('forbidden'):
        if item in ['.ththscrpt', '.ththconfig']:
            continue
        startingEntry = startingEntry + item + ','
    extensionsBox = tk.Entry(settingsWindow, font=('Microsoft Sans Serif', 13), width=40)
    extensionsBox.insert(0, startingEntry)
    extensionsBox.pack(padx=5, pady=5)
    saveButton = tk.Button(settingsWindow, text='Save', font=('Microsoft Sans Serif', 13), command=saveSettings)
    saveButton.pack(pady=(5,5))
    #passcode generator
    label3 = tk.Label(settingsWindow, text='Passcode Generator', font=('Microsoft Sans Serif', 14), bg=normalSideCol, fg=textColor)
    label3.pack(pady=(10,0))
    label4 = tk.Label(settingsWindow, text='Generate a safe 32-character passcode.', font=('Microsoft Sans Serif', 10), bg=normalSideCol, fg=textColor)
    label4.pack(pady=(0,2))
    passGenBox = tk.Entry(settingsWindow, font=('Microsoft Sans Serif', 13), width=40)
    passGenBox.pack(padx=5, pady=5)
    generateButton = tk.Button(settingsWindow, text='Generate', font=('Microsoft Sans Serif', 13), command=generatePasscode)
    generateButton.pack(pady=(5,5))
    storeButton = tk.Button(settingsWindow, text='Store In Desktop', font=('Microsoft Sans Serif', 13), command=saveToDesktop)
    storeButton.pack(pady=(5,5))
    label5 = tk.Label(settingsWindow, text='General Settings', font=('Microsoft Sans Serif', 14), bg=normalSideCol, fg=textColor)
    label5.pack(pady=(10,0))
    toggle1 = tk.Checkbutton(settingsWindow, text="Remember last-visited folder", font=('Microsoft Sans Serif', 10), var=enableLastVisited, bg=normalSideCol, fg=textColor, command=lastVisitedToggle, selectcolor=normalSideCol)
    toggle1.pack()
    toggle2 = tk.Checkbutton(settingsWindow, text="Automatically visit last visited folder on startup", font=('Microsoft Sans Serif', 10), var=enableAutoRefresh, bg=normalSideCol, fg=textColor, command=autoRefreshToggle, selectcolor=normalSideCol)
    toggle2.pack()
    shortButton = tk.Button(settingsWindow, text='Create Shortcut To Desktop', font=('Microsoft Sans Serif', 13), command=putShortcutToDesktop)
    shortButton.pack(pady=(5,5))

def addFilesIntoEncryptedFolder():
    global USEXOR
    USEXOR = True if globalCurrentDirectoryObject.encryptionMethod == 'XOR' else False

    if not checkPass():
        return
    if not messagebox.askokcancel('Encrypt and add files', 'In the following window, select the files you want to encrypt and add into the target folder.'):
        return
    fileList = list(filedialog.askopenfilenames(title='Select files to encrypt and add to target folder...'))
    for file in fileList:
        if file.endswith('.thth') or file.endswith('.ththscrpt'):
            messagebox.showerror('File not allowed', '.thth and .ththscrpt files are not allowed to be selected.')
            return
    fileList = [item.replace('/', '\\') for item in fileList]
    key = generateKey(passBox.get())
    window, label, bar = progressWindow(f'Encrypting and adding files into {globalCurrentDirectoryObject.name}...')
    filecount = 0
    for file in fileList:
        filename = file.split(sep="\\")[-1]
        label.config(text=f'Encrypting\n{filename}\n({filecount}/{len(fileList)})')
        numberOfChunks = ceil(os.path.getsize(file) / CHUNKSIZE)
        piece = (100/numberOfChunks)
        modifyByChunk(file, key, piece=piece, destinationFolder=globalCurrentDirectoryObject.path, progressBar=bar)
        bar['value'] = 0
        filecount+=1
    window.destroy()
    refreshListBox(None, globalCurrentDirectoryObject.path)

def removeFileFromEncryptedFolder():
    global USEXOR
    USEXOR = True if globalCurrentDirectoryObject.encryptionMethod == 'XOR' else False

    if not checkPass():
        return
    filename = globalCurrentlySelectedPath.split(sep="\\")[-1]
    key = generateKey(passBox.get())
    if not messagebox.askokcancel("Decrypt and move to folder...", f"This function decrypts {Cipher(key).decrypt(filename.removesuffix('.thth').encode()).decode()} only and moves it to a folder of your choice."):
        return
    chosenFolder = filedialog.askdirectory()
    if not chosenFolder:
        return
    destinationFolder = joinAddr(chosenFolder, "fromThoth")
    try:
        os.makedirs(destinationFolder)
    except:
        pass
    window, label, bar = progressWindow(f'Decrypting and moving files...')
    label.config(text=f"Decypting and moving {filename} to {chosenFolder}...")
    window.title("Decrypt to folder...")
    numberOfChunks = ceil(os.path.getsize(globalCurrentlySelectedPath) / CHUNKSIZE)
    piece = (100/numberOfChunks)
    modifyByChunk(globalCurrentlySelectedPath, key, textBox=None, piece=piece, progressBar=bar, makeCopy=False, destinationFolder=destinationFolder)
    selected_indices = dirlistbox.curselection()
    for index in selected_indices:
        dirlistbox.delete(index)
    refreshListBox(None, dirBox.get())
    window.destroy()

#function runs whenever something is selected from the listbox
def fileSelected(event):
    selected_index = dirlistbox.curselection()
    if selected_index:
        index = selected_index[0]
        global globalCurrentlySelectedPath
        globalCurrentlySelectedPath = globalTitlePathDict[dirlistbox.get(index)]
        if not isFile(globalCurrentlySelectedPath):
            lookInFolderButton.config(state='normal')
            renameButton.config(state='disabled')
        else:
            lookInFolderButton.config(state='disabled')
            if (not globalCurrentDirectoryObject.isEncrypted) or (globalCurrentDirectoryObject.isEncrypted and globalIsTranslatedBoolean):
                renameButton.config(state='normal')
        if globalIsTranslatedBoolean:
            removeFileButton.config(state='normal')
        else:
            removeFileButton.config(state='disabled')
        deleteFileButton.config(state='normal')
        print("Selected ", globalCurrentlySelectedPath)

#start whatever file/folder is being selected from the listbox
def startFile(event):
    global globalCurrentlySelectedPath
    global globalCurrentDirectoryObject
    global USEXOR
    USEXOR = True if globalCurrentDirectoryObject.encryptionMethod == 'XOR' else False

    path = globalCurrentlySelectedPath
    key = generateKey(passBox.get())
    if globalIsTranslatedBoolean and isFile(path):
        if checkPass():
            name = Cipher(key).decrypt(path.split(sep='\\')[-1].removesuffix('.thth').encode()).decode()
            window, label, progress = progressWindow(f'Opening {name}...')
            storedpath = oldModifyByChunk(path, key, USEXOR, destinationFolder=os.path.expanduser("~")+f"\AppData\Local\Thoth", makeCopy=True, progressBar=progress, label=label, root=root)
            window.destroy()
            os.system(f'start "" "{storedpath}"')
            if isinstance(storedpath, Exception): #some error handling i guess
                messagebox.showerror('Error', f'Error decrypting file: {Exception}')
                return
            disableWidgets((dirlistbox, dirBox, passBox, lookInFolderButton, findDirectoryButton, refreshButton, decryptFolderButton, renameButton, parentFolderButton, deleteFileButton, translateFolderButton, removeFileButton, addFilesButton))
            name = storedpath.split(sep='\\')[-1]
            if messagebox.askyesno(f"File opened: {name}", "Would you like to save changes made to the file? Only click 'Yes' if you have made changes."):
                window, label, progress = progressWindow(f'Saving {name}...')
                reEncryptSingleFile(storedpath, path, key, label=label, progressBar=progress, root=root)
                window.destroy()
            os.remove(storedpath)
            enableWidgets((dirlistbox, dirBox, passBox, findDirectoryButton, refreshButton, decryptFolderButton, parentFolderButton, translateFolderButton, addFilesButton))
            return
    index = dirlistbox.nearest(event.y)
    if index < 0:
        print('nothing selected')
        return
    selected_item = dirlistbox.get(index)
    filepath:str = globalTitlePathDict[selected_item]
    if filepath.endswith('.thth'):
        messagebox.showwarning('Opening encrypted file not reccommended', 'It is advised not to open an encrypted file as it would just show you useless scrambled info AND you run the risk of accidentally modifying the file, which might render it unrecoverable. If you want to open a single file at its encrypted state, click "Translate" first, then double click on your desired file.')
        return
    os.system(f'start "" "{filepath}"')

#from the current target folder, navigate to parent folder and set it as the target folder.
def gotoParentFolder():
    lastUnit = globalCurrentDirectoryObject.path.split(sep='\\')[-1]
    newPath = globalCurrentDirectoryObject.path.removesuffix('\\' + lastUnit)
    if refreshListBox(None, newPath) == 'NOTRECCOMMEND':
        return
    dirBox.delete(0, tk.END)
    dirBox.insert(0, newPath)
    lookInFolderButton.config(state='disabled')

def rightClick(event):
    index = dirlistbox.nearest(event.y)
    if index < 0:
        print('nothing selected')
        return
    selected = dirlistbox.get(index)
    global globalTitlePathDict
    name = globalTitlePathDict[selected].split(sep='\\')[-1]
    messagebox.showinfo(f"{name}: Full Path", f"{globalTitlePathDict[selected]}")

def savePasswordToDesktop():
    passw = passBox.get()
    if passw == "":
        messagebox.showerror('Empty password', 'No password entered, nothing to save.')
        return
    global globalCurrentDirectoryObject
    num = 1
    while os.path.exists(joinAddr(os.path.expanduser("~/Desktop"), f"{globalCurrentDirectoryObject.name}{num}.txt")):
        num+=1
    open(joinAddr(os.path.expanduser("~/Desktop"), f"{globalCurrentDirectoryObject.name}{num}.txt"), 'w').write(passw)
    messagebox.showinfo('Password saved!', f"Passcode saved on your desktop: {globalCurrentDirectoryObject.name}{num}.txt\nHide it before someone finds it!")

def hashFileContentsAsPassword():
    filesSelected = filedialog.askopenfilenames()
    if len(filesSelected) < 1:
        messagebox.showwarning("No files selected.", "No files are selected to hash and use as password, password box remains empty.")
        return
    messagebox.showinfo(f"{len(filesSelected)} files chosen", f"You have chosen the following files to be hashed and used as a password: {str([os.path.split(file)[-1] for file in filesSelected])}")
    whole_hash = hash_files(filesSelected)
    passBox.insert(0, whole_hash)

# GUI #######################################################################################################################################

root = tk.Tk()
root.title(f"ThothCrypt {globalVersionNumber}")
root.resizable(False, False)
centerWindow(root, 1045, 730)

normalListCol = '#001e21'
normalBGCol = '#003d45'
normalSideCol = '#00585f'
encrListCol = '#001737'
encrBGCol = '#00244a'
encrSideCol = '#002c5c'
textColor = 'white'
blueTextColor = '#96ffff'
greenTextColor = '#bdffe4'
purpleTextColor = '#a6ff47'
root.config(bg=normalSideCol)

#left frame, always here. parent is root
leftFrame = tk.Frame(root, bg=normalBGCol, width=600, height=800)
targetLabel = tk.Label(leftFrame, text='Target Folder', font=('Microsoft Sans Serif', 14), bg=normalBGCol, fg=textColor)
targetLabel.pack(pady=(10,2))

dirBox = tk.Entry(leftFrame, font=('Microsoft Sans Serif', 13), width=70)
dirBox.bind('<Return>', lambda e: refreshListBox(e, dirBox.get()))

dirBox.pack(padx=5, pady=5)
if saveload.getData("enableLastVisited"):
    lastVisited = saveload.getData(key="lastVisited")
    if lastVisited:
        dirBox.insert(0, lastVisited)

buttonLF = tk.Frame(leftFrame, bg=normalBGCol)
findDirectoryButton = tk.Button(buttonLF, text='Search for folder...', font=('Microsoft Sans Serif', 13), command=searchDirectory)
findDirectoryButton.grid(column=0, row=0, padx=5)
refreshButton = tk.Button(buttonLF, text='Refresh', font=('Microsoft Sans Serif', 13), command=lambda: refreshListBox(None, dirBox.get()))
refreshButton.grid(column=1, row=0, padx=5)
openFolderButton = tk.Button(buttonLF, text='Show in File Explorer', font=('Microsoft Sans Serif', 13), command=openFileExplorer)
openFolderButton.grid(column=2, row=0, padx=5)
settingsButton = tk.Button(buttonLF, text='Settings', font=('Microsoft Sans Serif', 13), command=openSettings)
settingsButton.grid(column=3, row=0, padx=5)
buttonLF.pack(padx=10, pady=10)

passcodeLabel = tk.Label(leftFrame, text='Encryption Passcode', font=('Microsoft Sans Serif', 14), bg=normalBGCol, fg=textColor)
passcodeLabel.pack()

passBox = tk.Entry(leftFrame, font=('Microsoft Sans Serif', 13), width=40, show='●')
passBox.pack(padx=5, pady=5)

passButtons = tk.Frame(leftFrame, bg=normalBGCol)
saveToDesktopButton = tk.Button(passButtons, text='Save to desktop', font=('Microsoft Sans Serif', 13), command=savePasswordToDesktop)
saveToDesktopButton.grid(column=0, row=0, padx=5)
getPassword = tk.Button(passButtons, text='Hash files as password', font=('Microsoft Sans Serif', 13), command=hashFileContentsAsPassword)
getPassword.grid(column=1, row=0, padx=5)
passButtons.pack(padx=10, pady=10)

#scrollable listbox
scrollbar = tk.Scrollbar(root, orient=tk.VERTICAL, width=20)
horizontalScrollBar = tk.Scrollbar(leftFrame, orient=tk.HORIZONTAL)
dirlistbox = tk.Listbox(
    leftFrame, yscrollcommand=scrollbar.set, xscrollcommand=horizontalScrollBar.set, selectmode=tk.SINGLE, width=100, height=20, font=('Consolas', 11),
    bg=normalListCol, fg=textColor, highlightbackground='black',
    selectbackground=greenTextColor, selectforeground=normalListCol, selectborderwidth=0,
)
horizontalScrollBar.config(command=dirlistbox.xview)
scrollbar.config(command=dirlistbox.yview)
dirlistbox.pack(padx=20, pady=(10,0), expand=False)
dirlistbox.pack_propagate(False)
horizontalScrollBar.pack(pady=(0,10), fill=tk.X, padx=20, expand=False)
horizontalScrollBar.pack_propagate(False)

dirlistbox.bind('<<ListboxSelect>>', fileSelected)
dirlistbox.bind('<Double-Button-1>', startFile)
dirlistbox.bind("<Button-3>", rightClick)

statusLabel = tk.Label(leftFrame, text=f"No file selected.", font=('Microsoft Sans Serif', 13), bg=normalBGCol, fg=textColor)
statusLabel.pack(pady=(0, 0))
statusLabel2 = tk.Label(leftFrame, text='', font=('Microsoft Sans Serif', 13), bg=normalBGCol, fg=textColor, width=75)
statusLabel2.pack(pady=(0, 10), expand=False)
statusLabel2.pack_propagate(False)

#first, pack the buttons that will be in BOTH encrypted and decrypted mode.
rightFrame = tk.Frame(root, bg=normalSideCol, width=200, height=800)
parentFolderButton = tk.Button(rightFrame, text='Parent Folder', font=('Microsoft Sans Serif', 13), command=gotoParentFolder)
parentFolderButton.pack(padx=15, pady=(14, 4))
lookInFolderButton = tk.Button(rightFrame, text='Look in Folder', font=('Microsoft Sans Serif', 13), command=lookInFolder)
lookInFolderButton.pack(padx=15, pady=(14, 4))
deleteFileButton = tk.Button(rightFrame, text='Delete', font=('Microsoft Sans Serif', 13), command=deleteSelectedFile, state='disabled', fg='red')
deleteFileButton.pack(padx=7, pady=(14, 4))
renameButton = tk.Button(rightFrame, text='Rename File', font=('Microsoft Sans Serif', 13), command=renameCurrentFile, state='disabled')
renameButton.pack(padx=7, pady=(14, 4))
#then, pack the exclusive buttons into seperate frames.
#when folder is normal, display normalButtonFrame
normalButtonFrame = tk.Frame(rightFrame, bg=normalSideCol)
encryptFolderButton = tk.Button(normalButtonFrame, text='Encrypt Folder', font=('Microsoft Sans Serif', 13), command=lambda: startModification(True), fg=encrListCol, bg=blueTextColor)
encryptFolderButton.pack(padx=15, pady=(14, 4))
#when folder is encrypted, display encrButtonFrame
encrButtonFrame = tk.Frame(rightFrame, bg=encrSideCol)
translateFolderButton = tk.Button(encrButtonFrame, text='Translate', font=('Microsoft Sans Serif', 13), command=translateListBox)
translateFolderButton.pack(padx=15, pady=(14, 4))
addFilesButton = tk.Button(encrButtonFrame, text='Encrypt and Add', font=('Microsoft Sans Serif', 13), command=addFilesIntoEncryptedFolder)
addFilesButton.pack(padx=15, pady=(14, 4))
removeFileButton = tk.Button(encrButtonFrame, text='Decrypt and Move', font=('Microsoft Sans Serif', 13), state='disabled',command=removeFileFromEncryptedFolder)
removeFileButton.pack(padx=15, pady=(14, 4))
decryptFolderButton = tk.Button(encrButtonFrame, text='Decrypt Folder', font=('Microsoft Sans Serif', 13), command=lambda: startModification(False), fg=normalListCol, bg=greenTextColor)
decryptFolderButton.pack(padx=15, pady=(14, 4))

leftFrame.grid(column=0, row=0, sticky=tk.N+tk.S+tk.E+tk.W)
scrollbar.grid(column=1, row=0, sticky=tk.N+tk.S+tk.E+tk.W)

if saveload.getData("enableAutoRefresh", False):
    if os.path.exists(dirBox.get()):
        refreshListBox(None, dirBox.get())

root.mainloop()