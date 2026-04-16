# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building SnapLoad (yt-dlp GUI) as a standalone .exe.

Usage:
    pyinstaller build.spec

This will produce:  dist/SnapLoad.exe
"""

import os

block_cipher = None

# Path to the source package
src_path = os.path.join("src", "ytdlp_gui")

a = Analysis(
    [os.path.join(src_path, "main.py")],
    pathex=["src"],
    binaries=[],
    datas=[
        # Bundle the assets folder
        (os.path.join(src_path, "assets"), os.path.join("ytdlp_gui", "assets")),
    ],
    hiddenimports=[
        "yt_dlp",
        "customtkinter",
        "PIL",
        "requests",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SnapLoad",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # Windowed mode (no terminal)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(src_path, "assets", "icon.ico"),
)
