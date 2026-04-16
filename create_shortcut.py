"""
create_shortcut.py — Creates a Windows shortcut (.lnk) with the app icon.

Run once to create a "SnapLoad" shortcut on your Desktop or in the project folder.

Usage:
    py create_shortcut.py             # Creates shortcut in project folder
    py create_shortcut.py --desktop   # Creates shortcut on Desktop
"""

import os
import sys
import subprocess


def create_shortcut(target_dir: str | None = None) -> None:
    """Create a Windows .lnk shortcut for SnapLoad."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    pyw_path = os.path.join(project_dir, "SnapLoad.pyw")
    icon_path = os.path.join(project_dir, "src", "ytdlp_gui", "assets", "icon.ico")

    # Determine where to put the shortcut
    if target_dir is None:
        target_dir = project_dir

    shortcut_path = os.path.join(target_dir, "SnapLoad.lnk")

    # Use PowerShell to create the shortcut (no external deps needed)
    ps_script = f"""
    $ws = New-Object -ComObject WScript.Shell
    $shortcut = $ws.CreateShortcut("{shortcut_path}")
    $shortcut.TargetPath = "pythonw.exe"
    $shortcut.Arguments = '"{pyw_path}"'
    $shortcut.WorkingDirectory = "{project_dir}"
    $shortcut.IconLocation = "{icon_path},0"
    $shortcut.Description = "SnapLoad — yt-dlp GUI"
    $shortcut.Save()
    """

    subprocess.run(
        ["powershell", "-Command", ps_script],
        check=True,
        capture_output=True,
    )
    print(f"[OK] Shortcut created: {shortcut_path}")


if __name__ == "__main__":
    if "--desktop" in sys.argv:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        create_shortcut(desktop)
    else:
        create_shortcut()
