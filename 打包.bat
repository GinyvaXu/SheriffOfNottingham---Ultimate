@echo off
rem One-click packaging into a folder build (dist\SheriffOfNottingham\ = exe + _internal\, includes assets\ and mods\)
rem The spec file embeds version info (version_info.txt) and the mods/ folder.
cd /d "%~dp0"
python -m PyInstaller --clean --noconfirm SheriffOfNottingham.spec
echo.
echo Done: folder build is at dist\SheriffOfNottingham\ (exe + _internal\)
echo Optional: build the installer with ISCC.exe installer.iss
pause