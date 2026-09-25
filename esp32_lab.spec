# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de configuration PyInstaller pour ESP32 MicroPython Lab
Auteur : Fares Bel Haj Ali
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

ROOT_DIR = Path.cwd()

# Fichiers de donnÃ©es et ressources Ã  embarquer
datas = [
    ('esp32_lab/resources', 'esp32_lab/resources'),
    ('examples', 'examples'),
    ('docs', 'docs'),
    ('LICENSE', '.'),
    ('README.md', '.'),
]

# Modules masquÃ©s ou dynamiques
hiddenimports = [
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
    'esp32_lab',
    'esp32_lab.app',
    'esp32_lab.app.theme',
    'esp32_lab.core',
    'esp32_lab.core.courses',
    'esp32_lab.core.evaluator',
    'esp32_lab.core.database',
    'esp32_lab.core.report_generator',
    'esp32_lab.core.examples',
    'esp32_lab.core.models',
    'esp32_lab.core.simulation',
    'esp32_lab.core.simulation.peripherals',
    'esp32_lab.core.simulation.peripherals.neopixel_ring',
    'esp32_lab.ui',
    'esp32_lab.ui.canvas',
    'esp32_lab.ui.canvas.components',
    'esp32_lab.ui.editor',
    'esp32_lab.ui.panels',
    'esp32_lab.ui.dialogs',
    'esp32_lab.ui.dialogs.courses_dialog',
    'esp32_lab.ui.dialogs.examples_dialog',
    'esp32_lab.ui.dialogs.about_dialog',
]
hiddenimports += collect_submodules('esp32_lab')


a_student = Analysis(
    ['run_student.py'],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a_teacher = Analysis(
    ['run_teacher.py'],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_student = PYZ(a_student.pure, a_student.zipped_data, cipher=block_cipher)
pyz_teacher = PYZ(a_teacher.pure, a_teacher.zipped_data, cipher=block_cipher)

exe_student = EXE(
    pyz_student,
    a_student.scripts,
    [],
    exclude_binaries=True,
    name='ESP32_Lab_Student',
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
    icon=str(ROOT_DIR / 'esp32_lab' / 'resources' / 'icons' / 'app_icon.ico'),
)

exe_teacher = EXE(
    pyz_teacher,
    a_teacher.scripts,
    [],
    exclude_binaries=True,
    name='ESP32_Lab_Teacher',
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
    icon=str(ROOT_DIR / 'esp32_lab' / 'resources' / 'icons' / 'app_icon.ico'),
)

coll_student = COLLECT(
    exe_student,
    a_student.binaries,
    a_student.zipfiles,
    a_student.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ESP32_Lab_Student',
)

coll_teacher = COLLECT(
    exe_teacher,
    a_teacher.binaries,
    a_teacher.zipfiles,
    a_teacher.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ESP32_Lab_Teacher',
)
