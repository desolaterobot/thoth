import os

def createShortcut(target:str, shortcutName:str, destinationFolder:str):
    shortcut = f"{shortcutName}.lnk"
    content = f'''@echo off
setlocal
set "TargetPath={target}"
set "ShortcutPath={shortcut}"
echo Set oWS = WScript.CreateObject("WScript.Shell")> CreateShortcut.vbs
echo sLinkFile = "%ShortcutPath%">> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile)>> CreateShortcut.vbs
echo oLink.TargetPath = "%TargetPath%">> CreateShortcut.vbs
echo oLink.Save>> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs
move {shortcut} {destinationFolder}
del "%~f0"
    '''
    open("shortcutCreator.bat", "w").write(content)
    os.startfile('shortcutCreator.bat')