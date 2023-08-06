# Named after the Egyptian god of sacred texts, ThothCrypt isn't far from mythology...

### ThothCrypt is a simple graphical program to encrypt entire folders just by using a single passcode, made in Python. Fernet encryption from the cryptography package is used for symmetric encryption and Tkinter is used to handle the GUI.

### 1. [Getting Started](#getting-started)
### 2. [Caveats](#caveats)
### 3. [Extra Features](#extra-features)
### 4. [How It Works](#how-it-works)

## Getting Started

### Target Directories

Upon opening the app, two text fields can be seen at the top. One for the Target Directory, and one for the chosen passcode. The first step is to choose a directory to encrypt. You could manually type out the path to your directory, but I'd imagine most people would click on `Search for folder...` which brings up a file explorer to select the folder graphically.

Sidenote: 'directory' and 'folder' are used interchangeably here.

### Folder content box

Once the target directory is selected, the gigantic list box below the two text fields will now be populated with the folder's contents. As with most folders, there are folders within folders within other folders... so how do we know which files or folder go where?

Whenever an item (file or folder) title is indented by 4 spaces, this means that this item is included in the above folder that is unindented, much like functions or loops in Python programming:

```
FOLDER 1/1: myfolder - contains 3 files, 1 folders:
    FILE 1/3: insideMyFolder.txt - 7KB
    FILE 2/3: insideMyFolder2.txt - 4KB
    FOLDER 1/1: nestedFolder - contains 1 files, 0 folders:
        FILE 1/1: insideNestedFolder.txt - 1.3KB 
    FILE 3/3: insideMyFolderAgain.txt - 7KB
```

The result is an efficient way to display nested folder contents - every item in the list box is either a file or a folder.

### Encryption

Once we are sure that the target folder is the folder we want to encrypt, we can start thinking of a passcode and typing it on the `Encryption Passcode` text field. As always, more secure passcodes have a mixture of numbers, upper and lowercase letters and symbols. However, in Thoth, password choices are not restricted. Any non-blank passcode can be used.

Once a passcode is entered, we can click on `Encrypt Folder` and begin encrypting the entire folder. It is that simple! EVERY file in the folder will be encrypted, even those within subfolders. The names of the subfolders remain the same though.

Once all files within the folder are encrypted, the app turns from <b>green to blue</b>. The color difference is to differentiate normal folders and encrypted folders: app turns <b>green</b> if target folder is unencrypted and turns <b>blue</b> if target folder is encrypted.

If we open the encrypted folder using the file explorer, we see that all of the filenames have turned into strings of random characters, appended with a .thth file extension. The encrypted folder also contains a small additional .ththscrpt file to mark it as encrypted. <b>DO NOT</b> delete this file or modify any of the encrypted files, as <b>any slight changes might render the encrypted files completely unrecoverable.</b>

### Decryption

If you want the folder back, you can follow the same steps as before, type in the same passcode that you used to encrypt the folder, then click on the `Decrypt Folder` button, and the entire target folder will be back to normal, untouched.

If you have an encrypted folder, but you only need to <u>gain access to a <b>single</b> file,</u> you can click on the `Translate` button, which will translate all of the encrypted filenames to their original names. You can now double click on one of the files, which would only encrypt and run <u>ONLY</u> the file you selected and ignoring the rest, saving time.

## Caveats

There are some drawbacks to consider with file encryption:

### Slow speed
Encryption isn't just opening and running a file - it scrambles the file contents reversibly according to a 32-bit key, a very complex process that can take up to minutes when a folder contains very large files.

### Size Bloat
Using Python's Fernet encryption, the size of the file contents increase by about 33.3%, this is because for every 3 bits of input, the encryption function spits out 4. I have ideas to implement a file compression algorithm but compression is likely to be ineffective due to the randomness of the contents, and it makes the entire process significantly slower if implemented.

### Memory Wear and Tear
The encryption process requires reading every single file in a folder, encrypting their contents, and writing all of those contents back into the same file locations. This may be a problem when using fragile memory mediums such as very old hard drives or SD Cards, as they may have slow or limited read/write cycles.

## Extra Features

### Renaming
The `Rename` button renames files or folders. 

### Running a File
Upon selection of a file, you can double click it to run the file, just like you would on a file explorer. Double-clicking on a folder opens the folder in a file explorer. Right-clicking each item displays the full path of the object selected.

### Deleting a File
Click the `Delete` button to remove a file. It can also remove entire folders and all of its contents.

### Translate Button
Appearing only when the target folder is encrypted, this button translates the gibberish of the encrypted filenames into its original names. Passcode is required for this. In the translated mode, the filenames turn from blue to green. In this mode, you can rename or open the files as per normal. However, if you opened the file and have made changes to the file you want saved, you MUST click 'Yes' on the dialog box that shows up after the file is opened: INSERT PICTURE

## How it works

### File Browsing
When the target folder is selected it lists out all the files within this folder using the following recursive function that takes in either a File or a Folder:
```python
def fileList(direct:Directory): #root Directory
    files = list()
    for item in direct.contents: #item can either be File or Directory
        itemPath = joinAddr(direct.path, item.name) #Path of this item
        if not isAllowed(itemPath):
            continue 
        if isFile(itemPath):
            files.append(itemPath) #add the filepath to the Files list
        else:
            recursed = fileList(item)
            files.extend(recursed)
    return files
```
In the aforementioned function, when the folder system is seen as a tree data structure with Files and Folders as nodes, the function traverses each branch, and backtracks to the last Folder when it sees a File. It stores the full path of every node on this tree. This process is called 'walking' through or looking through the folder, and could take some time depending on the number of files in the folder.

### Modification
'Modifying' in this context refers to either encrypting or decrypting. ThothCrypt uses Fernet encryption, included in the Python cryptography library. Fernet uses a 32-byte key, to modify content. Anyone who has this key would be able to decrypt your encrypted files and read them.

Since most of us are not expected to memorize a 32-byte (32 characters) passcode, ThothCrypt uses a hash function (SHA-256) that transforms any string into the 32-byte key that Fernet desires. This allows a more friendlier range of passcodes.

A hash function is a function that takes in an input string of any length and spits out a fixed length string. For example, the hash function used is SHA-256, which spits out a nearly unique 256-bit (32 bytes) string for any string input.

`passcode -> hashfunction() -> key used for modification`

Hash functions are irreversible, so it is near impossible to trace the input string of the hash function, just by knowing the hash result. It is important to know that if very simple input strings are used, it is possible to bruteforce hash results given enough time. Hence, it is advised to choose a complex passcode, though we do not try to limit you here.

### Modification of entire folders
When a folder begins modification, it looks through every single filepath stored earlier from walking through the file, and reads each of the files contents. For each file, it feeds the file contents into the Fernet encryption function mentioned earlier in order to output the encrypted contents into the same file. 
