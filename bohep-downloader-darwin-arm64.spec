# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('bohep_downloader/decode_packed.js', 'bohep_downloader'), ('bohep_downloader/decode_packed.js', '.')]
binaries = []
hiddenimports = ['bohep_downloader', 'bohep_downloader.downloader', 'encodings', 'encodings.aliases', 'encodings.utf_8', 'encodings.ascii', 'encodings.latin_1']
tmp_ret = collect_all('bohep_downloader')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['bohep_downloader/cli.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='bohep-downloader-darwin-arm64',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.icns'],
)
