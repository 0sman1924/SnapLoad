"""
run.pyw — Double-click launcher (no terminal window).

The .pyw extension tells Windows to use pythonw.exe,
which runs Python without opening a console window.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from ytdlp_gui.main import main

if __name__ == "__main__":
    main()
