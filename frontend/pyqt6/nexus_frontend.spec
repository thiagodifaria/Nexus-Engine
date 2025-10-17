# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Nexus Engine PyQt6 Frontend.

This spec file configures how PyInstaller creates a standalone executable
for the Nexus Engine trading platform desktop application.

Usage:
    pyinstaller nexus_frontend.spec

The resulting executable will be in the dist/ directory.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Project root
project_root = os.path.abspath(os.path.join(SPECPATH, '..', '..'))
backend_root = os.path.join(project_root, 'backend', 'python')
frontend_root = os.path.join(project_root, 'frontend', 'pyqt6')

# Collect all frontend source files
a = Analysis(
    [os.path.join(frontend_root, 'src', 'main.py')],
    pathex=[
        frontend_root,
        os.path.join(frontend_root, 'src'),
        backend_root,
        os.path.join(backend_root, 'src'),
    ],
    binaries=[],
    datas=[
        # Frontend resources
        (os.path.join(frontend_root, 'resources'), 'resources'),

        # Backend configuration
        (os.path.join(backend_root, 'config', '.env.example'), 'config'),

        # Documentation (optional, for help menu)
        (os.path.join(project_root, 'README.md'), 'docs'),
    ],
    hiddenimports=[
        # PyQt6 modules
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtCharts',

        # Backend modules
        'domain',
        'domain.entities',
        'domain.value_objects',
        'domain.repositories',
        'application',
        'application.usecases',
        'application.services',
        'infrastructure',
        'infrastructure.adapters',
        'infrastructure.database',
        'infrastructure.telemetry',

        # Market data providers
        'finnhub',
        'alpha_vantage',
        'nasdaq_data_link',
        'fredapi',

        # Database
        'sqlalchemy',
        'alembic',
        'psycopg2',

        # Telemetry
        'prometheus_client',
        'pythonjsonlogger',
        'opentelemetry',

        # Utilities
        'pydantic',
        'python_dotenv',
        'websocket',

        # Plotting
        'pyqtgraph',
        'matplotlib',
        'numpy',
        'pandas',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test modules
        'tests',
        'pytest',
        'pytest_cov',
        'pytest_asyncio',

        # Exclude development tools
        'black',
        'isort',
        'mypy',
        'ruff',

        # Exclude unnecessary packages
        'tkinter',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Priority for binary files
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NexusEngine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(frontend_root, 'resources', 'icons', 'nexus_icon.ico') if os.path.exists(os.path.join(frontend_root, 'resources', 'icons', 'nexus_icon.ico')) else None,
)

# Collect all binaries and dependencies
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NexusEngine',
)

# macOS .app bundle (optional, only on macOS)
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='NexusEngine.app',
        icon=os.path.join(frontend_root, 'resources', 'icons', 'nexus_icon.icns') if os.path.exists(os.path.join(frontend_root, 'resources', 'icons', 'nexus_icon.icns')) else None,
        bundle_identifier='com.nexusengine.trading',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
        },
    )