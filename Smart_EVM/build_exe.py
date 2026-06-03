"""
build_exe.py — called by make_exe.bat to build launch.exe via PyInstaller.
Using Python instead of pure batch avoids all path-with-spaces quoting issues.
"""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(HERE, "icon.ico")
LAUNCH = os.path.join(HERE, "launch.pyw")

# Clean previous build artefacts so a changed icon is always applied.
import shutil
for path in [
    os.path.join(HERE, "launch.exe"),
    os.path.join(HERE, "build", "work", "launch"),
    os.path.join(HERE, "build", "launch.spec"),
    os.path.join(HERE, "launch.spec"),
]:
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)

print()
if os.path.isfile(ICON):
    print("  icon.ico found -- building with custom icon.")
    # --icon sets the exe file icon shown in Explorer/taskbar
    # --add-data bundles the .ico so Qt can load it as the window icon at runtime
    icon_args = ["--icon", ICON, "--add-data", f"{ICON};."]
else:
    print("  icon.ico not found -- building without icon.")
    print("  To add a custom icon: place icon.ico in this folder and re-run.")
    icon_args = []

print()
print("  Building launch.exe -- please wait (1-3 minutes)...")
print()

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--noconsole",
    "--name", "launch",
    "--distpath", HERE,
    "--workpath", os.path.join(HERE, "build", "work"),
    "--specpath", os.path.join(HERE, "build"),
    "--hidden-import", "PyQt6.QtCore",
    "--hidden-import", "PyQt6.QtGui",
    "--hidden-import", "PyQt6.QtWidgets",
    "--hidden-import", "matplotlib.backends.backend_qtagg",
    "--hidden-import", "websockets",
    "--hidden-import", "openpyxl",
] + icon_args + [LAUNCH]

result = subprocess.run(cmd, cwd=HERE)
sys.exit(result.returncode)
