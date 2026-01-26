#!/bin/bash
# LiteType Launcher
# Double-click this file to start the voice-to-text app

cd "$(dirname "$0")"
source venv/bin/activate
python run.py
