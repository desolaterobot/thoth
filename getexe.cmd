pyinstaller --noconfirm --onefile --console --icon %cd%python\assets\icon.ico %cd%\encr.py
del "encr.spec"
rmdir /s /q build
move %cd%\dist\encr.exe %cd%
rmdir /s /q dist