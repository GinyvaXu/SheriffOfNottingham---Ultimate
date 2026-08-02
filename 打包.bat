@echo off
rem One-click packaging into a single exe (output to dist\, includes assets\ fonts)
cd /d "%~dp0"
python -m PyInstaller --onefile --windowed --clean --noconfirm --name "SheriffOfNottingham" --add-data "assets;assets" main.py
echo.
echo Done: exe is at dist\SheriffOfNottingham.exe
pause