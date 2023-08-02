#main script: renders window and GUI functions

import tkinter as tk
from tkinter import filedialog
from fileclass import *
import sys
from tkinter import messagebox
import time

# GLOBAL VARIABLES ######################################################################################

globalVersionNumber = '1.0'
globalTitlePathDict = dict()
globalCurrentlySelectedPath:str = None
globalCurrentDirectoryObject:Directory = None

# FUNCTIONS #############################################################################################

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
        normalButtonFrame.pack()
    else:
        encrButtonFrame.pack()

def hideRightFrame():
    rightFrame.grid_forget()

def showListBox(listbox:tk.Listbox, items:list):
    listbox.delete(0, 'end')
    for item in items:
        listbox.insert(tk.END, item)

def appendListBox(listbox:tk.Listbox, item: str):
    listbox.insert(tk.END, item)

def changeStatusLabel(directory:Directory):
    size = sizeToString(directory.getSize())
    name = directory.name
    dircount = directory.totalDirCount
    filecount = directory.totalFileCount
    completefilecount = len(directory.getCompleteFilePathList())
    statusLabel.config(text=f'{name} has {filecount} files, {dircount} subfolders. Including subfolders, {completefilecount} files with total size {size}')
    showRightFrame(True)
    deleteFileButton.config(state='disabled')

#function is RECURSIVE! 
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
    global globalCurrentDirectoryObject
    globalCurrentDirectoryObject = targetDirectory
    return targetDirectory

def showStatus(directory):
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
    statusLabel2.config(text=f'Time taken to walk through {directory}: {(endTime-startTime):.3g} seconds.')
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
    filepath = filedialog.askdirectory(title='select directory')
    showListBox(dirlistbox, [])
    print(filepath)
    if filepath == '':
        hideRightFrame()
        return
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
#TODO make a seperate modification window, then call the function there.
def startModification(isEncrypting:bool):
    def 
    global globalCurrentDirectoryObject
    if passBox.get() == "":
        messagebox.showerror(title='No passcode entered', message=f"Please enter a passcode before you {'encrypt' if isEncrypting else 'decrypt'}.")
        return 
    #delete this
    if not messagebox.askokcancel(title=f"Confirm {'encryption' if isEncrypting else 'decryption'}", message=f"You are about to {'encrypt' if isEncrypting else 'decrypt'} the folder {globalCurrentDirectoryObject.path} with the given passcode. Proceed?"):
        return
    #modification window
    modWindow = tk.Toplevel(root)
    centerWindow(modWindow, 200, 100)
    modWindow.title(f"{'Encrypting' if isEncrypting else 'Decrypting'} files...")
    textBox = tk.Label(modWindow, text=f"You are about to {'encrypt' if isEncrypting else 'decrypt'} the folder\n{globalCurrentDirectoryObject.path}\nwith the given passcode. Proceed?")
    textBox.pack(padx=10, pady=10)
    encryptButton = tk.Button(rightFrame, text=f"Start {'Encryption' if isEncrypting else 'Decryption'}", font=('Arial', 13), command=)
    encryptButton.pack(padx=15, pady=(14, 4))
    #encryption steps: modification, update current directory, update the list box.
    key = generateKey(passBox.get())
    currentDirectory = globalCurrentDirectoryObject.path
    global globalCurrentModificationProgess
    globalCurrentModificationProgess = 0
    globalCurrentDirectoryObject.modifyDirectory(isEncrypting, key) #modification
    #for the modification stage, find a way to 
    globalCurrentDirectoryObject = path2Dir(currentDirectory) #upodating current directory
    refreshListBox(None, currentDirectory) #update listbox
    modWindow.destroy()

#such a tedious process for something that is not really related to encryption
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
    
#GUI######################################################################################

root = tk.Tk()
root.title(f"Thoth {globalVersionNumber}")
root.resizable(False, False)
#centerWindow(root, 840, 600)

bgColor = '#02262b'
normalBgColor = '#02191c'
listBoxColor = '#000e26'
textColor = 'white'

#left frame, always here. parent is root
leftFrame = tk.Frame(root, bg=bgColor, width=600, height=800)
label = tk.Label(leftFrame, text='Target Folder', font=('Arial', 14), bg=bgColor, fg=textColor)
label.pack(pady=(10,2))

dirBox = tk.Entry(leftFrame, font=('Arial', 13), width=70)
dirBox.bind('<Return>', lambda e: refreshListBox(e, dirBox.get()))
dirBox.pack(padx=5, pady=5)

findDirectoryButton = tk.Button(leftFrame, text='Search for folder...', font=('Arial', 13), command=searchDirectory)
findDirectoryButton.pack(padx=5, pady=5)

label = tk.Label(leftFrame, text='Encryption Passcode', font=('Arial', 14), bg=bgColor, fg=textColor)
label.pack()

passBox = tk.Entry(leftFrame, font=('Arial', 13), width=30, show='●')
passBox.pack(padx=5, pady=5)
#scrollable listbox
scrollbar = tk.Scrollbar(root, orient=tk.VERTICAL, width=20)
horizontalScrollBar = tk.Scrollbar(leftFrame, orient=tk.HORIZONTAL)
dirlistbox = tk.Listbox(
    leftFrame, yscrollcommand=scrollbar.set, xscrollcommand=horizontalScrollBar.set, selectmode=tk.SINGLE, width=100, height=20, font=('Consolas', 11),
    bg=listBoxColor, fg=textColor, highlightbackground='black'
    )
horizontalScrollBar.config(command=dirlistbox.xview)
scrollbar.config(command=dirlistbox.yview)
dirlistbox.pack(padx=20, pady=(10,0))
horizontalScrollBar.pack(pady=(0,10), fill=tk.X, padx=20)

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

def startFile(event):
    index = dirlistbox.nearest(event.y)
    if index < 0:
        print('nothing selected')
        return
    selected_item = dirlistbox.get(index)
    os.system(f'start "" "{globalTitlePathDict[selected_item]}"')

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

statusLabel = tk.Label(leftFrame, text='No Folder Displayed.', font=('Arial', 13), bg=bgColor, fg=textColor)
statusLabel.pack(pady=(0, 10))
statusLabel2 = tk.Label(leftFrame, text='', font=('Arial', 13), bg=bgColor, fg=textColor)
statusLabel2.pack(pady=(0, 10))

#first, pack the buttons that will be in BOTH encrypted and decrypted mode.
rightFrame = tk.Frame(root, bg=normalBgColor, width=200, height=800)
parentFolderButton = tk.Button(rightFrame, text='Parent Folder', font=('Arial', 13), command=gotoParentFolder)
parentFolderButton.pack(padx=15, pady=(14, 4))
lookInFolderButton = tk.Button(rightFrame, text='Look in Folder', font=('Arial', 13), command=lookInFolder)
lookInFolderButton.pack(padx=15, pady=(14, 4))
deleteFileButton = tk.Button(rightFrame, text='Delete', font=('Arial', 13), command=deleteSelectedFile, state='disabled', fg='red')
deleteFileButton.pack(padx=7, pady=(14, 4))

#then, pack the exclusive buttons into seperate frames.
#when folder is normal, display normalButtonFrame
normalButtonFrame = tk.Frame(rightFrame, bg=normalBgColor)
renameButton = tk.Button(normalButtonFrame, text='Rename', font=('Arial', 13), command=renameCurrentFile, state='disabled')
renameButton.pack(padx=7, pady=(14, 4))
encryptFolderButton = tk.Button(normalButtonFrame, text='Encrypt Folder', font=('Arial', 13), command=lambda: startModification(True))
encryptFolderButton.pack(padx=15, pady=(14, 4))
#when folder is encrypted, display encrButtonFrame
encrButtonFrame = tk.Frame(rightFrame, bg=normalBgColor)
decryptFolderButton = tk.Button(encrButtonFrame, text='Decrypt Folder', font=('Arial', 13))
decryptFolderButton.pack(padx=15, pady=(15, 7))
translateFolderButton = tk.Button(encrButtonFrame, text='Translate Folder', font=('Arial', 13))
translateFolderButton.pack(padx=15, pady=7)
decryptSingleButton = tk.Button(encrButtonFrame, text='Decrypt File and Open', font=('Arial', 13))
decryptSingleButton.pack(padx=15, pady=7)

leftFrame.grid(column=0, row=0, sticky=tk.N+tk.S+tk.E+tk.W)
scrollbar.grid(column=1, row=0, sticky=tk.N+tk.S+tk.E+tk.W)

root.mainloop()