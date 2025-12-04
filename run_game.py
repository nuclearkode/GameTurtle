#!/usr/bin/env python3
"""
Robo-Arena Launcher

Run this script to start the game:
    python run_game.py
"""

import sys
import os

# Ensure the workspace is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.main import main

if __name__ == "__main__":
    main()
