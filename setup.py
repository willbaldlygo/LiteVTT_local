"""
py2app setup script for VTT Local.
Build with: python setup.py py2app
"""

from setuptools import setup

APP = ['run.py']
DATA_FILES = [
    ('models', ['models/ggml-base.bin']),
]
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'VTT Local',
        'CFBundleDisplayName': 'VTT Local',
        'CFBundleIdentifier': 'com.local.vtt',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # Menu bar app (no dock icon)
        'NSMicrophoneUsageDescription': 'VTT Local needs microphone access to record your voice for transcription.',
        'NSAppleEventsUsageDescription': 'VTT Local needs accessibility access for global hotkeys and text insertion.',
    },
    'packages': ['vtt', 'rumps', 'pynput', 'sounddevice', 'numpy', 'pywhispercpp'],
    'includes': ['cffi', 'pyobjc'],
}

setup(
    app=APP,
    name='VTT Local',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
