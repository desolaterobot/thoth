#main script: renders window and GUI functions

from tkinter import ttk
import tkinter as tk
from tkinter import filedialog
from fileclass import *
import saveload
from tkinter import messagebox
import time

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

globalTotalFilesFound = 0

# function is RECURSIVE! 
def showDirectory(e, directory:str, nestvalue:int=0):
    global globalCurrentDirectoryObject
    targetDirectory = path2Dir(directory)
    fileCount = 0
    dirCount = 0
    global globalTotalFilesFound
    for item in targetDirectory.contents:
        statusLabel2.config(text=f'{item.name} discovered.')
        if isinstance(item, File):
            globalTotalFilesFound += 1
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
        statusLabel.config(text=f'Searching target folder... {globalTotalFilesFound} files found so far.')
        root.update()
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
    global globalTotalFilesFound
    globalTotalFilesFound = 0
    global globalIsTranslatedBoolean
    globalIsTranslatedBoolean = False
    lookInFolderButton.config(state='disabled')
    renameButton.config(state='disabled')
    deleteFileButton.config(state='disabled')
    dirBox.delete(0, tk.END)
    dirBox.insert(0, directory)
    time.sleep(0.1)
    startTime = time.time()
    dirBox.config(state='disabled')
    findDirectoryButton.config(state='disabled')
    refreshButton.config(state='disabled')
    changeStatusLabel(showDirectory(None, directory))
    refreshButton.config(state='normal')
    findDirectoryButton.config(state='normal')
    dirBox.config(state='normal')
    endTime = time.time()
    #apparently '.3g' is the 3sf specifier????
    statusLabel2.config(text=f'Time taken to walk through {directory}: {(endTime-startTime):.3g} seconds.', fg='white')
    #change listbox color based on if file is encrypted or not.s
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
    #check if the folder is the C drive itself or directly nested in the C: drive or C:\Users\name.
    #I assume there are more 'crucial' folders but this should be enough, I put full trust in the user to encrypt responsibly
    if directory.endswith(':') or directory == os.path.expanduser("~") or len(directory.split('\\')) == 2:
        if not messagebox.askyesno(f"Dangerous folder", f"Thoth does not reccommend encrypting or even looking into {directory} due to its size and importance. Look into it anyway?"):
            return 'NOTRECCOMMEND'
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

#binded to the button that says "Encrypt folder"
#the folder encryption function here is non-recursive, unlike the object method modifyDirectory(), to better interact with tkinter widgets.
def startModification(isEncrypting:bool):
    def start():
        modWindow.title(f"{'Encrypting' if isEncrypting else 'Decrypting'} files...")
        encryptButton.pack_forget()
        textBox.config(text='\nIt seems like modification cannot start for some reason.\nRefreshing and trying again...')
        #encryption steps: modification, update current directory, update the list box.
        key = generateKey(passBox.get())
        global globalCurrentDirectoryObject
        currentDirectory = globalCurrentDirectoryObject.path
        startTime = time.time() #*START OF MODIFICATION PROCESS ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        try:
            fileList = globalCurrentDirectoryObject.getCompleteFilePathList()
        except:
            refreshListBox(None, dirBox.get())
            start()
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
    centerWindow(modWindow, 500, 120)
    modWindow.title(f"Confirm {'Encryption' if isEncrypting else 'Decryption'}")
    textBox = tk.Label(modWindow, text=f"You are about to {'encrypt' if isEncrypting else 'decrypt'} the folder\n{globalCurrentDirectoryObject.path}\nwith the given passcode. Proceed?", font=('Microsoft Sans Serif', 12))
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
        newNameAndExtension = newName + extension
        newName2 = newNameAndExtension
        if globalIsTranslatedBoolean: #! before renaming the encrypted file, we must first encrypt the new name.
            newNameAndExtension = Fernet(encryptionKey).encrypt(newNameAndExtension.encode()).decode() + '.thth'
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
            newText = itemSelected.replace(Fernet(encryptionKey).decrypt(name.removesuffix('.thth').encode()).decode(), newName2)
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
        messagebox.showerror('Attempting to rename encrypted file', 'It is not advised that you rename an encrypted file. If you want to rename an encrypted file at its normal state, click on "Translate", select the desired file, then click on "Rename" again.')
        return
    extension = os.path.splitext(name)[1] #gets the file extension from the pure filename
    if globalIsTranslatedBoolean: #! if file is encrypted, to get the extension, remove the .thth suffix first, decrypt the name, then get extension.
        extension = os.path.splitext(Fernet(encryptionKey).decrypt(name.removesuffix('.thth').encode()).decode())[1] #getting the extension if name is encrypted
    #creating the toplevel window
    renameWindow = tk.Toplevel(root)
    centerWindow(renameWindow, 300, 120)
    renameWindow.title("Rename file/folder")
    label = tk.Label(renameWindow, text=f"Enter the new name for {name if not globalIsTranslatedBoolean else Fernet(encryptionKey).decrypt(name.removesuffix('.thth').encode()).decode()}.\nFile extension added automatically.")
    label.pack(pady=5, padx=10)
    nameEntry = tk.Entry(renameWindow, width=40, bg='#bababa')
    nameEntry.pack(pady=5, padx=10)
    nameEntry.focus_set()
    nameEntry.bind()
    nameEntry.bind("<Return>", onSubmit)
    okButton = tk.Button(renameWindow, text='Rename', font=('Arial', 10), command=onSubmit)
    okButton.pack(pady=5)

# GUI #######################################################################################################################################

root = tk.Tk()
root.title(f"ThothCrypt {globalVersionNumber}")
root.resizable(False, False)
centerWindow(root, 1020, 675)

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

buttonLF = tk.Frame(leftFrame, bg=normalBGCol)
findDirectoryButton = tk.Button(buttonLF, text='Search for folder...', font=('Microsoft Sans Serif', 13), command=searchDirectory)
findDirectoryButton.grid(column=0, row=0, padx=5)
refreshButton = tk.Button(buttonLF, text='Refresh', font=('Microsoft Sans Serif', 13), command=lambda: refreshListBox(None, dirBox.get()))
refreshButton.grid(column=1, row=0, padx=5)
""" settingsButton = tk.Button(buttonLF, text='Settings', font=('Microsoft Sans Serif', 13), command=lambda: refreshListBox(None, dirBox.get()))
settingsButton.grid(column=2, row=0, padx=5) """
buttonLF.pack(padx=10, pady=10)

passcodeLabel = tk.Label(leftFrame, text='Encryption Passcode', font=('Microsoft Sans Serif', 14), bg=normalBGCol, fg=textColor)
passcodeLabel.pack()

passBox = tk.Entry(leftFrame, font=('Microsoft Sans Serif', 13), width=30, show='●')
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
dirlistbox.pack(padx=20, pady=(10,0), expand=False)
dirlistbox.pack_propagate(False)
horizontalScrollBar.pack(pady=(0,10), fill=tk.X, padx=20, expand=False)
horizontalScrollBar.pack_propagate(False)

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
    global globalCurrentlySelectedPath
    path = globalCurrentlySelectedPath
    if globalIsTranslatedBoolean and isFile(path):
        if checkPass():
            dirlistbox.config(state='disabled')
            storedpath = decryptSingleFile(path, generateKey(passBox.get()))
            if isinstance(storedpath, Exception): #some error handling
                messagebox.showerror('Error', f'Error decrypting file: {Exception}')
                dirlistbox.config(state='normal')
                return
            #at this moment, data is being stored in an internal folder in the computer. if user makes any changes to this file, ask if they want to save these changes into encryption folder.
            #the reason why this happens is to reduce time taken, by skipping re-encryption after user is done with the file, whereever necessary.
            #also useful with reducing read/write wear and tear if user stores encrypted data on a sensitive memory device, such as SD Cards, old HDD's
            if messagebox.askyesno('Save changes into encrypted folder', 'Would you like to save any changes made to the previously opened file?'):
                reEncryptSingleFile(storedpath, path, generateKey(passBox.get()))
            dirlistbox.config(state='normal')
            os.remove(storedpath)
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

dirlistbox.bind('<<ListboxSelect>>', fileSelected)
dirlistbox.bind('<Double-Button-1>', startFile)
dirlistbox.bind("<Button-3>", rightClick)

statusLabel = tk.Label(leftFrame, text='No Folder Displayed.', font=('Microsoft Sans Serif', 13), bg=normalBGCol, fg=textColor)
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
renameButton = tk.Button(rightFrame, text='Rename', font=('Microsoft Sans Serif', 13), command=renameCurrentFile, state='disabled')
renameButton.pack(padx=7, pady=(14, 4))
#then, pack the exclusive buttons into seperate frames.
#when folder is normal, display normalButtonFrame
normalButtonFrame = tk.Frame(rightFrame, bg=normalSideCol)
encryptFolderButton = tk.Button(normalButtonFrame, text='Encrypt Folder', font=('Microsoft Sans Serif', 13), command=lambda: startModification(True), fg=encrListCol, bg=blueTextColor)
encryptFolderButton.pack(padx=15, pady=(14, 4))
#when folder is encrypted, display encrButtonFrame
encrButtonFrame = tk.Frame(rightFrame, bg=encrSideCol)
translateFolderButton = tk.Button(encrButtonFrame, text='Translate', font=('Microsoft Sans Serif', 13), command=translateListBox)
translateFolderButton.pack(padx=15, pady=(15, 7))
decryptFolderButton = tk.Button(encrButtonFrame, text='Decrypt Folder', font=('Microsoft Sans Serif', 13), command=lambda: startModification(False), fg=normalListCol, bg=greenTextColor)
decryptFolderButton.pack(padx=15, pady=7)

leftFrame.grid(column=0, row=0, sticky=tk.N+tk.S+tk.E+tk.W)
scrollbar.grid(column=1, row=0, sticky=tk.N+tk.S+tk.E+tk.W)

root.mainloop()