# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Collect all DLLs, .pyd extensions, data files (models/templates/resources),
# and hidden imports for dynamsoft_capture_vision_bundle so they are bundled
# into the executable and available at runtime via sys._MEIPASS.
dcvb_datas, dcvb_binaries, dcvb_hiddenimports = collect_all('dynamsoft_capture_vision_bundle')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=dcvb_binaries,
    datas=dcvb_datas,  # config.json is NOT embedded — distribute it next to the exe so users can edit the license key
    hiddenimports=dcvb_hiddenimports + [
        # Dynamsoft sub-modules loaded dynamically at runtime
        'dynamsoft_capture_vision_bundle',
        'dynamsoft_capture_vision_bundle.core',
        'dynamsoft_capture_vision_bundle.cvr',
        'dynamsoft_capture_vision_bundle.dbr',
        'dynamsoft_capture_vision_bundle.dcp',
        'dynamsoft_capture_vision_bundle.dcpd',
        'dynamsoft_capture_vision_bundle.ddn',
        'dynamsoft_capture_vision_bundle.dip',
        'dynamsoft_capture_vision_bundle.dlr',
        'dynamsoft_capture_vision_bundle.id_utility',
        'dynamsoft_capture_vision_bundle.license',
        'dynamsoft_capture_vision_bundle.utility',
        # Other runtime dependencies
        'cv2',
        'numpy',
        'requests',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# One-file executable: all binaries and datas are embedded in the EXE.
# On first run the files are extracted to a temporary directory (sys._MEIPASS).
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='IPCameraViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
