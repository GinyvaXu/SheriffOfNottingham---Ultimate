@echo off
rem One-click packaging into a single exe (output to dist\, includes assets\ and mods\)
rem The spec file embeds version info (version_info.txt) and the mods/ folder.
cd /d "%~dp0"
python -m PyInstaller --clean --noconfirm SheriffOfNottingham.spec
echo.
echo Done: exe is at dist\SheriffOfNottingham.exe
echo Optional: build the installer with ISCC.exe installer.iss
pause