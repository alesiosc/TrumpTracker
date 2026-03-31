# -*- mode: python ; coding: utf-8 -*-

datas = [('.env', '.')]


a = Analysis(
    ['tracker.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['DrissionPage', 'curl_cffi'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'tensorflow', 'scipy', 'matplotlib', 'pandas', 'numpy',
        'PIL', 'cv2', 'sklearn', 'IPython', 'notebook', 'jupyter',
        'playwright', 'scrapling', 'camoufox',
    ],
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
    name='TrumpTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['trump_icon.ico'],
)
