#main script: renders window and GUI functions

from tkinter import ttk
import tkinter as tk
from tkinter import filedialog
from fileclass import *
import saveload
import sys
from tkinter import messagebox
import time
from cryptography import fernet

# GLOBAL VARIABLES ######################################################################################

globalVersionNumber = '1.0'
globalTitlePathDict = dict()
globalCurrentlySelectedPath:str = None
globalCurrentDirectoryObject:Directory = None
globalIsTranslatedBoolean = False
globalWrongTries = saveload.getData('wrongTries', 0)

# FUNCTIONS #############################################################################################

#includes the 'wrong passcode' message window if passcode is false.
def checkPass():
    #!check if the given key is correct by checking if the md5 hash of the given key matches the hash in thoth script.
    givenHash = eval(open(joinAddr(globalCurrentDirectoryObject.path, f"{globalCurrentDirectoryObject.name}.ththscrpt"), "r").read())['hash']
    key = generateKey(passBox.get())
    hashKey = mdHash(key.decode())
    if hashKey != givenHash:
        global globalWrongTries
        globalWrongTries += 1
        saveload.setData('wrongTries', globalWrongTries)
        messagebox.showerror('Wrong passcode', f'The passcode entered does not match the passcode used for the encryption of this folder. Number of wrong attempts to access this folder: {globalWrongTries}')
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
                decryptedFileName = Fernet(generateKey(passBox.get())).decrypt(encryptedFileName.encode()).decode() #contains the original extension
                newTitle = title.replace(encryptedFileName + ".thth", decryptedFileName)
                newTitles.append(newTitle)
                newDict[newTitle] = path
            else:
                newTitles.append(title)
                newDict[title] = path
        dirlistbox.config(fg=purpleTextColor)
        globalTitlePathDict = newDict
        #showing the listbox with updated titles.
        showListBox(dirlistbox, newTitles)
        statusLabel2.config(text="Translated encrypted names into their original names.", fg=purpleTextColor)
    else:
        refreshListBox(None, globalCurrentDirectoryObject.path)
        dirlistbox.config(fg=blueTextColor)
    globalIsTranslatedBoolean = not globalIsTranslatedBoolean

def centerWindow(window, width, height):
    # Get the screen width and height
    screenW = window.winfo_screenwidth()
    screenH = window.winfo_screenheight()
    x = (screenW // 2) - (width // 2)
    y = (screenH // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

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

# function is RECURSIVE! 
def showDirectory(e, directory:str, nestvalue:int=0):
    targetDirectory = path2Dir(directory)
    fileCount = 0
    dirCount = 0
    for item in targetDirectory.contents:
        if isinstance(item, File):
            fileCount += 1
            title = f"{nestvalue * '    '}FILE {fileCount}/{targetDirectory.totalFileCount}: {item.name} - {sizeToString(item.getSize())}"
            appendListBox(dirlistbox, title)
            globalTitlePathDict[title] = item.path
        elif isinstance(item, Directory):
            dirCount += 1
            title = f"{nestvalue * '    '}FOLDER {dirCount}/{targetDirectory.totalDirCount}: {item.name} - contains {item.totalFileCount} files, {item.totalDirCount} folders:" 
            appendListBox(dirlistbox, title)
            globalTitlePathDict[title] = item.path
            showDirectory(None, item.path, nestvalue + 1)
        root.update()
    global globalCurrentDirectoryObject
    globalCurrentDirectoryObject = targetDirectory
    return targetDirectory

#display status of target file on the label text at the bottom
def showStatus(directory):
    def changeStatusLabel(directory:Directory):
        size = sizeToString(directory.getSize())
        name = directory.name
        dircount = directory.totalDirCount
        filecount = directory.totalFileCount
        completefilecount = len(directory.getCompleteFilePathList())
        statusLabel.config(text=f'{name} has {filecount} files, {dircount} subfolders. Including subfolders, {completefilecount} files with total size {size}')
        showRightFrame(not directory.isEncrypted)
        deleteFileButton.config(state='disabled')
    lookInFolderButton.config(state='disabled')
    renameButton.config(state='disabled')
    deleteFileButton.config(state='disabled')
    dirBox.delete(0, tk.END)
    dirBox.insert(0, directory)
    statusLabel.config(text=f'Searching {directory}...')
    time.sleep(0.1)
    startTime = time.time()
    changeStatusLabel(showDirectory(None, directory))
    endTime = time.time()
    #apparently '.3g' is the 3sf specifier????
    statusLabel2.config(text=f'Time taken to walk through {directory}: {(endTime-startTime):.3g} seconds.', fg='white')
    #change listbox color based on if file is encrypted or not.
    if globalCurrentDirectoryObject.isEncrypted:
        dirlistbox.config(bg=encrListCol, fg=blueTextColor, selectbackground=blueTextColor, selectforeground=encrListCol)
        leftFrame.config(bg=encrBGCol)
        rightFrame.config(bg=encrSideCol)
        statusLabel.config(bg=encrBGCol)
        statusLabel2.config(bg=encrBGCol)
        targetLabel.config(bg=encrBGCol)
        passcodeLabel.config(bg=encrBGCol)
    else:
        dirlistbox.config(bg=normalListCol, fg=greenTextColor, selectbackground=greenTextColor, selectforeground=normalListCol)
        leftFrame.config(bg=normalBGCol)
        rightFrame.config(bg=normalSideCol)
        statusLabel.config(bg=normalBGCol)
        statusLabel2.config(bg=normalBGCol)
        targetLabel.config(bg=normalBGCol)
        passcodeLabel.config(bg=normalBGCol)
    return

#show the selected directory again, referring to the textbox instead of the directory finder
def refreshListBox(e, directory:str):
    #check if the folder is the C drive itself or directly nested in the C: drive or C:\Users\name.
    #I assume there are more 'crucial' folders but this should be enough, I put full trust in the user to encrypt responsibly
    if directory.endswith(':') or directory == os.path.expanduser("~") or len(directory.split('\\')) == 2:
        if not messagebox.askyesno(f"Dangerous folder", f"Thoth does not reccommend encrypting or even looking into {directory} due to its size and importance. Look into it anyway?"):
            return
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
    if filepath == '':
        return
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

#binded to the button that says "Encrypt folder"
#the folder encryption function here is non-recursive, unlike the method modifyDirectory(), to better interact with tkinter widgets.
def startModification(isEncrypting:bool):
    def start():
        modWindow.title(f"{'Encrypting' if isEncrypting else 'Decrypting'} files...")
        encryptButton.pack_forget()
        textBox.config(text='\nDo not close this window.\nTime taken may vary depending\non file size and storage type.')
        #encryption steps: modification, update current directory, update the list box.
        key = generateKey(passBox.get())
        global globalCurrentDirectoryObject
        currentDirectory = globalCurrentDirectoryObject.path
        startTime = time.time() #*START OF MODIFICATION PROCESS ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        fileList = globalCurrentDirectoryObject.getCompleteFilePathList()
        folderList = globalCurrentDirectoryObject.getCompleteFolderPathList()
        thisPath = globalCurrentDirectoryObject.path
        thisName = globalCurrentDirectoryObject.name
        folderList.append(thisPath)
        totalFileNum = len(fileList)
        encryptionProgress = 1
        failureCount = 0
        thothInfo = {
            "hash" : None
        }

        progressBar = ttk.Progressbar(modWindow, orient='horizontal', length=300, mode='determinate')
        progressBar.pack(padx=5, pady=(8, 8))

        if isEncrypting:
            #!before we encrypt, check if this folder already contains files encrypted by Thoth.
            #!folders are considered encrypted ONLY when they contain the Thoth script.
            if os.path.exists(joinAddr(thisPath, f"{thisName}.ththscrpt")):
                messagebox.showerror('Folder is already encrypted.', 'No need to encrypt it again!')
            #!write the md5 hash of the key into the thoth template
            thothInfo['hash'] = mdHash(key.decode())
        else:
            #!before we decrypt, check if thoth script exists in the current folder.
            if not os.path.exists(joinAddr(thisPath, f"{thisName}.ththscrpt")):
                messagebox.showerror('This folder is not yet encrypted by Thoth', 'Hence, this cannot be decrypted.')
            givenHash = eval(open(joinAddr(thisPath, f"{thisName}.ththscrpt"), "r").read())['hash']
            hashKey = mdHash(key.decode())
            if hashKey != givenHash:
                print(f"Wrong key given for folder {thisName}")
            
        for filePath in fileList:
            message = f"Now {'encrypting:' if isEncrypting else 'decrypting:'}\n{filePath}\n({sizeToString(os.path.getsize(filePath))}) Progress:{encryptionProgress}/{totalFileNum}"
            progressBar['value'] += (100 / totalFileNum)
            e = modifyFile(isEncrypting, filePath, key)
            print(message)
            textBox.config(text=message)
            root.update()
            if isinstance(e, Exception):
                failureCount += 1
                messagebox.showerror(f'Error: {e}', f'Error modifying {filePath}')
            encryptionProgress += 1
        
        if isEncrypting:
            #!after encryption... we save the data into a .ththscrpt file in each subfolder, to signify an encryption by Thoth
            for folderPath in folderList:
                textBox.config(text=f"Placing folder data...\n{folderPath}")
                root.update()
                name = folderPath.split(sep='\\')[-1]
                open(joinAddr(folderPath, f"{name}.ththscrpt"), "w").write(str(thothInfo))
        else:
            #!after decryption... we remove the .ththscrpt file entirely in each subfolder, to show that the folder is normal.
            for folderPath in folderList:
                name = folderPath.split(sep='\\')[-1]
                os.remove(joinAddr(folderPath, f"{name}.ththscrpt"))

        endTime = time.time() #*END OF MODIFICATION PROCESS //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        globalCurrentDirectoryObject = path2Dir(currentDirectory) #updating current directory
        refreshListBox(None, currentDirectory) #update listbox
        statusLabel2.config(text=f"Time taken to {'encrypt' if isEncrypting else 'decrypt'} target directory: {(endTime-startTime):.3g} seconds.", fg='white')
        modWindow.destroy()
    global globalCurrentDirectoryObject
    if passBox.get() == "":
        messagebox.showerror(title='No passcode entered', message=f"Please enter a passcode before you {'encrypt' if isEncrypting else 'decrypt'}.")
        return 
    if not isEncrypting:
        if not checkPass():
            return
    #modification window
    modWindow = tk.Toplevel(root)
    centerWindow(modWindow, 500, 130)
    modWindow.title(f"Confirm {'Encryption' if isEncrypting else 'Decryption'}")
    textBox = tk.Label(modWindow, text=f"You are about to {'encrypt' if isEncrypting else 'decrypt'} the folder\n{globalCurrentDirectoryObject.path}\nwith the given passcode. Proceed?", font=('Arial', 10))
    textBox.pack(padx=5, pady=(5, 5))
    encryptButton = tk.Button(modWindow, text=f"Start {'Encryption' if isEncrypting else 'Decryption'}", font=('Arial', 13), command=start)
    encryptButton.pack(padx=5, pady=(5, 2))
    encryptButton.focus()

#such a tedious function for something that is not really related to encryption
def renameCurrentFile():
    def onSubmit(e=None):
        #renaming
        newName = nameEntry.get()
        if newName == "":
            messagebox.showerror("Name not entered", "You cannot have a blank filename wtf")
            return
        newPath = globalCurrentlySelectedPath.replace(name, newName+extension)
        renameWindow.destroy()
        os.rename(globalCurrentlySelectedPath, newPath)
        selected = dirlistbox.curselection()
        #changing the listbox
        if not selected:
            return
        itemSelected:str = dirlistbox.get(selected[0])
        newText = itemSelected.replace(name, newName+extension)
        dirlistbox.delete(selected[0])
        dirlistbox.insert(selected[0], newText)
        #change the key-value pair in the globalDictionary
        globalTitlePathDict[newText] = globalTitlePathDict.pop(itemSelected)
        globalTitlePathDict[newText] = newPath
    name = globalCurrentlySelectedPath.split('\\')[-1]
    extension = os.path.splitext(name)[1]
    renameWindow = tk.Toplevel(root)
    centerWindow(renameWindow, 300, 120)
    renameWindow.title("Rename file/folder")
    label = tk.Label(renameWindow, text=f"Enter the new name for {name}.\nFile extension added automatically.")
    label.pack(pady=5, padx=10)
    nameEntry = tk.Entry(renameWindow, width=40, bg='#bababa')
    nameEntry.pack(pady=5, padx=10)
    nameEntry.focus_set()
    nameEntry.bind()
    nameEntry.bind("<Return>", onSubmit)
    okButton = tk.Button(renameWindow, text='Rename', font=('Arial', 10), command=onSubmit)
    okButton.pack(pady=5)

# GUI ##################################################################################################

root = tk.Tk()
root.title(f"Thoth {globalVersionNumber}")
root.resizable(False, False)
centerWindow(root, 1015, 665)

normalListCol = '#001e21'
normalBGCol = '#003d45'
normalSideCol = '#00585f'
encrListCol = '#001737'
encrBGCol = '#00244a'
encrSideCol = '#002c5c'
textColor = 'white'
blueTextColor = '#96ffff'
greenTextColor = '#bdffe4'
purpleTextColor = '#96ffb2'
root.config(bg=normalSideCol)

#left frame, always here. parent is root
leftFrame = tk.Frame(root, bg=normalBGCol, width=600, height=800)
targetLabel = tk.Label(leftFrame, text='Target Folder', font=('Arial', 14), bg=normalBGCol, fg=textColor)
targetLabel.pack(pady=(10,2))

dirBox = tk.Entry(leftFrame, font=('Arial', 13), width=70)
dirBox.bind('<Return>', lambda e: refreshListBox(e, dirBox.get()))
dirBox.pack(padx=5, pady=5)

findDirectoryButton = tk.Button(leftFrame, text='Search for folder...', font=('Arial', 13), command=searchDirectory)
findDirectoryButton.pack(padx=5, pady=5)

passcodeLabel = tk.Label(leftFrame, text='Encryption Passcode', font=('Arial', 14), bg=normalBGCol, fg=textColor)
passcodeLabel.pack()

passBox = tk.Entry(leftFrame, font=('Arial', 13), width=30, show='●')
passBox.pack(padx=5, pady=5)
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
dirlistbox.pack(padx=20, pady=(10,0))
horizontalScrollBar.pack(pady=(0,10), fill=tk.X, padx=20)

#function runs whenever something is selected from the listbox
def fileSelected(event):
    selected_index = dirlistbox.curselection()
    if selected_index:
        index = selected_index[0]
        global globalCurrentlySelectedPath
        globalCurrentlySelectedPath = globalTitlePathDict[dirlistbox.get(index)]
        if not isFile(globalCurrentlySelectedPath):
            lookInFolderButton.config(state='normal')
        else:
            lookInFolderButton.config(state='disabled')
        deleteFileButton.config(state='normal')
        renameButton.config(state='normal')
        print("Selected ", globalCurrentlySelectedPath)

#start whatever file/folder is being selected from the listbox
def startFile(event):
    index = dirlistbox.nearest(event.y)
    if index < 0:
        print('nothing selected')
        return
    selected_item = dirlistbox.get(index)
    os.system(f'start "" "{globalTitlePathDict[selected_item]}"')

#from the current target folder, navigate to parent folder and set it as the target folder.
def gotoParentFolder():
    dirBox.delete(0, tk.END)
    lastUnit = globalCurrentDirectoryObject.path.split(sep='\\')[-1]
    newPath = globalCurrentDirectoryObject.path.removesuffix('\\' + lastUnit)
    dirBox.delete(0, tk.END)
    dirBox.insert(0, newPath)
    refreshListBox(None, newPath)
    lookInFolderButton.config(state='disabled')

dirlistbox.bind('<<ListboxSelect>>', fileSelected)
dirlistbox.bind('<Double-Button-1>', startFile)

statusLabel = tk.Label(leftFrame, text='No Folder Displayed.', font=('Arial', 13), bg=normalBGCol, fg=textColor)
statusLabel.pack(pady=(0, 10))
statusLabel2 = tk.Label(leftFrame, text='', font=('Arial', 13), bg=normalBGCol, fg=textColor)
statusLabel2.pack(pady=(0, 10))

#first, pack the buttons that will be in BOTH encrypted and decrypted mode.
rightFrame = tk.Frame(root, bg=normalSideCol, width=200, height=800)
parentFolderButton = tk.Button(rightFrame, text='Parent Folder', font=('Arial', 13), command=gotoParentFolder)
parentFolderButton.pack(padx=15, pady=(14, 4))
lookInFolderButton = tk.Button(rightFrame, text='Look in Folder', font=('Arial', 13), command=lookInFolder)
lookInFolderButton.pack(padx=15, pady=(14, 4))
deleteFileButton = tk.Button(rightFrame, text='Delete', font=('Arial', 13), command=deleteSelectedFile, state='disabled', fg='red')
deleteFileButton.pack(padx=7, pady=(14, 4))

#then, pack the exclusive buttons into seperate frames.
#when folder is normal, display normalButtonFrame
normalButtonFrame = tk.Frame(rightFrame, bg=normalSideCol)
renameButton = tk.Button(normalButtonFrame, text='Rename', font=('Arial', 13), command=renameCurrentFile, state='disabled')
renameButton.pack(padx=7, pady=(14, 4))
encryptFolderButton = tk.Button(normalButtonFrame, text='Encrypt Folder', font=('Arial', 13), command=lambda: startModification(True), fg=encrListCol, bg=blueTextColor)
encryptFolderButton.pack(padx=15, pady=(14, 4))
#when folder is encrypted, display encrButtonFrame
encrButtonFrame = tk.Frame(rightFrame, bg=encrSideCol)
translateFolderButton = tk.Button(encrButtonFrame, text='Translate', font=('Arial', 13), command=translateListBox)
translateFolderButton.pack(padx=15, pady=(15, 7))
decryptFolderButton = tk.Button(encrButtonFrame, text='Decrypt Folder', font=('Arial', 13), command=lambda: startModification(False), fg=normalListCol, bg=greenTextColor)
decryptFolderButton.pack(padx=15, pady=7)

leftFrame.grid(column=0, row=0, sticky=tk.N+tk.S+tk.E+tk.W)
scrollbar.grid(column=1, row=0, sticky=tk.N+tk.S+tk.E+tk.W)

root.mainloop()