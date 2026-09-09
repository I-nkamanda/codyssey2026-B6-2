#!/usr/bin/env python3
"""AI-based Git Commit & PR Generator CLI Launcher."""

import sys
import os

# Ensure package root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_gitgen.cli import main #ai_getgen.cli.main

if __name__ == "__main__":
    main()
