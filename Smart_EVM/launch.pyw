"""
launch.pyw — SMART EVM Silent Launcher

Running this with pythonw.exe (which Windows does automatically for .pyw
files when double-clicked) starts the app with NO console window.

Also used by make_exe.bat to build launch.exe via PyInstaller.
Works both as a plain .pyw script AND as a PyInstaller bundle because
it uses a direct import instead of runpy.run_path (which breaks in
frozen executables).
"""
import os
import sys

# ── Fix working directory ────────────────────────────────────────────
# sys.executable points to the .exe in a bundle, so use __file__ when
# available, otherwise fall back to the exe path.
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = os.path.dirname(os.path.abspath(sys.executable))

os.chdir(_HERE)
sys.path.insert(0, _HERE)

# ── Activate venv site-packages (only used when running as .pyw script,
#    not inside a PyInstaller bundle where packages are already embedded)
_venv_site = os.path.join(_HERE, ".venv", "Lib", "site-packages")
if os.path.isdir(_venv_site) and _venv_site not in sys.path:
    sys.path.insert(0, _venv_site)

# ── Import and run ───────────────────────────────────────────────────
# Direct import works in both script mode and PyInstaller frozen mode.
from main import main
main()
