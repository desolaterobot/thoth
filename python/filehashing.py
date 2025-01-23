import os
from tkinter import filedialog
from tkinter import messagebox
import hashlib

def file_select():
    try:
        return filedialog.askopenfilenames()
    except:
        messagebox.showerror("ERROR", "Error selecting files.")

def hash_files(file_paths:list):
    hash_obj = hashlib.sha256()
    for file in file_paths:
        with open(file, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
    return hash_obj.hexdigest()

if __name__ == "__main__":
    files = file_select()
    print(files)
    print(hash_files(files))