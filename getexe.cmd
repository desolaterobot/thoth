pyinstaller --noconfirm --onefile --windowed --icon "%cd%\python\assets\icon.ico" "%cd%\python\thoth.py"
del "thoth.spec"
rmdir /s /q build
move %cd%\dist\thoth.exe %cd%
rmdir /s /q dist