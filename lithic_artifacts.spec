# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Lithic Artifacts.
# Build with:  just build
#
# pyinstaller is a dev dependency — install with: uv sync
#
from PyInstaller.utils.hooks import collect_all

# Pull in everything pyxel needs (native libs, default assets, etc.)
pyxel_datas, pyxel_binaries, pyxel_hiddenimports = collect_all("pyxel")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=pyxel_binaries,
    datas=pyxel_datas,
    hiddenimports=pyxel_hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name="LithicArtifacts",
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # TODO: add icon path when art exists
)
