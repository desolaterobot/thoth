#main script: renders window and control flow

import tkinter as tk
from fileclass import *
import sys

versionNumber = '1.0'

root = tk.Tk()
root.title(f"Thoth {versionNumber}")
root.geometry("800x400")
root.resizable(width=False, height=False)

leftSide = tk.Frame(root, width=600, height=400, bg='#236375')
leftSide.grid(row=0, column=0)

rightEncr = tk.Frame(root, width=200, height=400, bg='#0c3861')
rightEncr.grid(row=0, column=1)

root.mainloop()