#main script: renders window and GUI functions

import tkinter as tk
from tkinter import filedialog
from fileclass import *
import sys

#GLOBAL VARIABLES######################################################################################

globalVersionNumber = '1.0'
globalTitlePathDict = dict()
globalCurrentlySelectedPath:str = None
globalCurrentDirectoryPath:str = None

#FUNCTIONS#############################################################################################

def onHoverDeleteButton(event, isShowing:bool):
    if isShowing:
        print(f"delete {globalCurrentlySelectedPath}?")
    else:
        print("left delete button")

def showRightFrame(isNormal):
    if isNormal:
        normalFrame.grid(column=1, row=0, sticky=tk.N+tk.S+tk.E+tk.W)
    else:
        encryptedFrame.grid(column=1, row=0, sticky=tk.N+tk.S+tk.E+tk.W)

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
    global globalCurrentDirectoryPath
    globalCurrentDirectoryPath = directory.path
    size = sizeToString(directory.getSize())
    name = directory.name
    dircount = directory.totalDirCount
    filecount = directory.totalFileCount
    statusLabel.config(text=f'{name} contains {filecount} files, {dircount} subfolders, with size {size}')
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
            title = f"{nestvalue * '    '}FOLDER {dirCount}/{targetDirectory.totalDirCount}: {item.name}"
            appendListBox(dirlistbox, title)
            globalTitlePathDict[title] = item.path
            showDirectory(None, item.path, nestvalue + 1)
    return targetDirectory

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
        showListBox(dirlistbox, [f'Folder "{directory}" does not exist. Did you type it correctly?'])
        return
    changeStatusLabel(showDirectory(None, directory))

def searchDirectory():
    globalTitlePathDict.clear()
    showListBox(dirlistbox, [])
    filepath = filedialog.askdirectory(title='select directory')
    print(filepath)
    if filepath == '':
        return
    filepath = filepath.replace('/', '\\')
    dirBox.delete(0, tk.END)  
    dirBox.insert(0, filepath) 
    changeStatusLabel(showDirectory(None, filepath))

def deleteSelectedFile():
    from shutil import rmtree
    if isFile(globalCurrentlySelectedPath):
        os.remove(globalCurrentlySelectedPath)
    else:
        rmtree(globalCurrentlySelectedPath)
    refreshListBox(None, globalCurrentDirectoryPath)

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
label.pack()

dirBox = tk.Entry(leftFrame, font=('Arial', 13), width=70)
dirBox.bind('<Return>', lambda e: refreshListBox(e, dirBox.get()))
dirBox.pack(padx=5, pady=5)

findDirectoryButton = tk.Button(leftFrame, text='Search for folder...', font=('Arial', 13), command=searchDirectory)
findDirectoryButton.pack(padx=5, pady=5)

label = tk.Label(leftFrame, text='Encryption Passcode', font=('Arial', 14), bg=bgColor, fg=textColor)
label.pack()

passBox = tk.Entry(leftFrame, font=('Arial', 13), width=50)
passBox.pack(padx=5, pady=5)
#scrollable listbox
scrollbar = tk.Scrollbar(leftFrame, orient=tk.VERTICAL)
dirlistbox = tk.Listbox(
    leftFrame, yscrollcommand=scrollbar.set, selectmode=tk.SINGLE, width=100, height=20, font=('Consolas', 11),
    bg=listBoxColor, fg=textColor, highlightbackground='black'
    )
scrollbar.config(command=dirlistbox.yview)
dirlistbox.pack(padx=20, pady=10)

def fileSelected(event):
    selected_index = dirlistbox.curselection()
    if selected_index:
        index = selected_index[0]
        global globalCurrentlySelectedPath
        globalCurrentlySelectedPath = globalTitlePathDict[dirlistbox.get(index)]
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

statusLabel = tk.Label(leftFrame, text='No Folder Displayed.', font=('Arial', 14), bg=bgColor, fg=textColor)
statusLabel.pack(pady=(0, 10))

#frame of buttons if target directory is encrypted. parent is root.
encryptedFrame = tk.Frame(root, bg=normalBgColor, width=200, height=800)
decryptFolderButton = tk.Button(encryptedFrame, text='Decrypt Folder', font=('Arial', 13))
decryptFolderButton.pack(padx=15, pady=(15, 7))
translateFolderButton = tk.Button(encryptedFrame, text='Translate Folder', font=('Arial', 13))
translateFolderButton.pack(padx=15, pady=7)
decryptFolderButton = tk.Button(encryptedFrame, text='Decrypt File and Open', font=('Arial', 13))
decryptFolderButton.pack(padx=15, pady=7)
deleteFileButton1 = tk.Button(encryptedFrame, text='Delete', font=('Arial', 13), command=deleteSelectedFile, state='disabled', fg='red')
deleteFileButton1.pack(padx=15, pady=7)
deleteFileButton1.bind("<Enter>", lambda e: onHoverDeleteButton(e, True))
deleteFileButton1.bind("<Leave>", lambda e: onHoverDeleteButton(e, False))

#frame of buttons if target directory is normal. parent is root.
normalFrame = tk.Frame(root, bg=normalBgColor, width=200, height=800)
encryptFolderButton = tk.Button(normalFrame, text='Encrypt Folder', font=('Arial', 13))
encryptFolderButton.pack(padx=15, pady=(15, 7))
openFileButton = tk.Button(normalFrame, text='Open File', font=('Arial', 13))
openFileButton.pack(padx=15, pady=7)
deleteFileButton2 = tk.Button(normalFrame, text='Delete', font=('Arial', 13), command=deleteSelectedFile, state='disabled', fg='red')
deleteFileButton2.pack(padx=15, pady=7)
deleteFileButton2.bind("<Enter>", lambda e: onHoverDeleteButton(e, True))
deleteFileButton2.bind("<Leave>", lambda e: onHoverDeleteButton(e, False))

leftFrame.grid(column=0, row=0, sticky=tk.N+tk.S+tk.E+tk.W)

root.mainloop()