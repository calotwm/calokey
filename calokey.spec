# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for CaloKey — a one-dir, windowed Windows bundle.

Builds a single-folder distribution under ``dist/calokey/`` whose entry point
is ``calokey.exe``. ``src/`` is placed on the module search path so the app's
absolute imports (``from config import store``, ``from state import AppState``,
``from midi import device``, ``from ui.app import App``) resolve exactly as
they do when running from source.

pygame is collected in full (``collect_all``) so the PortMidi native library
(``portmidi.dll``) and pygame's bundled data files ship with the executable.
"""

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# Bundle pygame data + native libs (portmidi.dll) and expose its submodules.
for package in ("pygame",):
    p_datas, p_binaries, p_hidden = collect_all(package)
    datas += p_datas
    binaries += p_binaries
    hiddenimports += p_hidden

# mido is byte-parse only, but include it for completeness of the import graph.
for package in ("mido",):
    p_datas, p_binaries, p_hidden = collect_all(package)
    datas += p_datas
    binaries += p_binaries
    hiddenimports += p_hidden

a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="calokey",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # windowed app; no console window on launch
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="calokey",
)
