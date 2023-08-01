#main script: renders window and GUI functions

import tkinter as tk
from tkinter import filedialog
from fileclass import *
import sys
from tkinter import messagebox

#GLOBAL VARIABLES######################################################################################

globalVersionNumber = '1.0'
globalTitlePathDict = dict()
globalCurrentlySelectedPath:str = None
globalCurrentDirectoryObject:Directory = None

#FUNCTIONS#############################################################################################

def onHoverDeleteButton(event, isShowing:bool):
    if isShowing:
        print(f"delete {globalCurrentlySelectedPath}?")
    else:
        print("left delete button")

def showRightFrame(isNormal):
    if isNormal:
        normalFrame.grid(column=2, row=0, sticky=tk.N+tk.S+tk.E+tk.W)
    else:
        encryptedFrame.grid(column=2, row=0, sticky=tk.N+tk.S+tk.E+tk.W)

def hideRightFrame():
    normalFrame.grid_forget()
    encryptedFrame.grid_forget()

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
    deleteFileButton1.config(state='disabled')
    deleteFileButton2.config(state='disabled')

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
    statusLabel.config(text=f'Searching {directory}...')
    return

def refreshListBox(e, directory:str):
    globalTitlePathDict.clear()
    showListBox(dirlistbox, [])
    #check if directory is empty
    if directory == "":
        hideRightFrame()
        return
    #check if given directory exists
    if not os.path.exists(directory):
        hideRightFrame()
        print(f"{directory} does not exist. Type another directory.")
        messagebox.showerror(title='Does not exist', message=f'Folder "{directory}" does not exist. Did you type it correctly?')
        return
    showStatus(directory)
    changeStatusLabel(showDirectory(None, directory))

def searchDirectory():
    globalTitlePathDict.clear()
    filepath = filedialog.askdirectory(title='select directory')
    showListBox(dirlistbox, [])
    print(filepath)
    if filepath == '':
        return
    filepath = filepath.replace('/', '\\')
    showStatus(filepath)
    dirBox.delete(0, tk.END)  
    dirBox.insert(0, filepath) 
    changeStatusLabel(showDirectory(None, filepath))

def deleteSelectedFile():
    if messagebox.askyesno(title='Confirm deletion', message=f'Are you sure you want to permanently delete {globalCurrentlySelectedPath}'):
        from shutil import rmtree
        if isFile(globalCurrentlySelectedPath):
            os.remove(globalCurrentlySelectedPath)
        else:
            try:
                rmtree(globalCurrentlySelectedPath)
            except PermissionError:
                messagebox.showerror(title='Permission error', message=f'Unable to access {globalCurrentlySelectedPath}')
        refreshListBox(None, globalCurrentDirectoryObject.path)

def lookInFolder():
    dirBox.delete(0, tk.END)
    dirBox.insert(0, globalCurrentlySelectedPath)
    refreshListBox(None, globalCurrentlySelectedPath)

def startEncryption():
    if not messagebox.askokcancel(title='Confirm encryption', message=f'You are about to encrypt the folder {globalCurrentDirectoryObject.path}. Proceed?'):
        return
    

#GUI######################################################################################

root = tk.Tk()
root.title(f"Thoth {globalVersionNumber}")
root.resizable(False, False)

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
            lookInFolderButton2.config(state='normal')
            lookInFolderButton1.config(state='normal')
        else:
            lookInFolderButton2.config(state='disabled')
            lookInFolderButton1.config(state='disabled')
        deleteFileButton2.config(state='normal')
        deleteFileButton1.config(state='normal')
        print("Selected ", globalCurrentlySelectedPath)

def startFile(event):
    index = dirlistbox.nearest(event.y)
    if index < 0:
        print('nothing selected')
        return
    selected_item = dirlistbox.get(index)
    os.system(f'start "" "{globalTitlePathDict[selected_item]}"')

dirlistbox.bind('<<ListboxSelect>>', fileSelected)
dirlistbox.bind('<Double-Button-1>', startFile)

statusLabel = tk.Label(leftFrame, text='No Folder Displayed.', font=('Arial', 13), bg=bgColor, fg=textColor)
statusLabel.pack(pady=(0, 10))

#frame of buttons if target directory is encrypted. parent is root.
encryptedFrame = tk.Frame(root, bg=normalBgColor, width=200, height=800)
decryptFolderButton = tk.Button(encryptedFrame, text='Decrypt Folder', font=('Arial', 13))
decryptFolderButton.pack(padx=15, pady=(15, 7))
translateFolderButton = tk.Button(encryptedFrame, text='Translate Folder', font=('Arial', 13))
translateFolderButton.pack(padx=15, pady=7)
decryptSingleButton = tk.Button(encryptedFrame, text='Decrypt File and Open', font=('Arial', 13))
decryptSingleButton.pack(padx=15, pady=7)
lookInFolderButton1 = tk.Button(encryptedFrame, text='Look in Folder', font=('Arial', 13), command=lambda e: lookInFolder(e, globalCurrentlySelectedPath), state='disabled')
lookInFolderButton1.pack(padx=15, pady=(15, 7))
deleteFileButton1 = tk.Button(encryptedFrame, text='Delete', font=('Arial', 13), command=deleteSelectedFile, state='disabled', fg='red')
deleteFileButton1.pack(padx=15, pady=7)

#frame of buttons if target directory is normal. parent is root.
normalFrame = tk.Frame(root, bg=normalBgColor, width=200, height=800)
encryptFolderButton = tk.Button(normalFrame, text='Encrypt Folder', font=('Arial', 13), command=startEncryption)
encryptFolderButton.pack(padx=15, pady=(14, 4))
lookInFolderButton2 = tk.Button(normalFrame, text='Look in Folder', font=('Arial', 13), command=lookInFolder)
lookInFolderButton2.pack(padx=15, pady=(14, 4))
deleteFileButton2 = tk.Button(normalFrame, text='Delete', font=('Arial', 13), command=deleteSelectedFile, state='disabled', fg='red')
deleteFileButton2.pack(padx=7, pady=(14, 4))

leftFrame.grid(column=0, row=0, sticky=tk.N+tk.S+tk.E+tk.W)
scrollbar.grid(column=1, row=0, sticky=tk.N+tk.S+tk.E+tk.W)

root.mainloop()