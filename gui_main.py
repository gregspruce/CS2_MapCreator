"""
CS2 Heightmap Generator - GUI Entry Point

Launch script for the graphical user interface.

Usage:
    python gui_main.py

Why separate entry point:
- Clean separation of CLI and GUI modes
- Easy to add command-line args later
- Standard pattern (main.py for CLI, gui_main.py for GUI)
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from src.gui import HeightmapGUI


def main():
    """
    Main entry point for GUI application.

    Steps:
    1. Create GUI instance
    2. Start Tkinter main loop
    3. Handle cleanup on exit

    Error handling:
    - Catch import errors (missing dependencies)
    - Catch Tkinter errors (display issues)
    - Provide helpful error messages
    """
    try:
        # Create and run GUI
        app = HeightmapGUI()
        app.mainloop()

    except ImportError as e:
        print("ERROR: Missing required dependencies")
        print(f"  {e}")
        print("\nPlease install requirements:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        print("ERROR: Failed to start GUI")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
