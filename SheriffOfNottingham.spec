# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('mods', 'mods')],
    hiddenimports=['tkinter', 'tkinter.filedialog'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SheriffOfNottingham',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='assets/icon.ico',
)

# Onedir build: python312.dll and all bundled files live in a permanent
# ``_internal`` folder next to the exe instead of a %TEMP%\_MEI extraction
# dir. This structurally eliminates the onefile bootloader failures
# ("Failed to load Python DLL ... python312.dll" after an update-restart and
# "Failed to remove temporary directory ... _MEIxxxxxx" on exit) that were
# caused by antivirus/Smart App Control racing the temp extraction or by
# file handles held into the temp dir.
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SheriffOfNottingham',
)
