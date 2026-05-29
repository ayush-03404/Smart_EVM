' ============================================================
' launch.vbs  -  SMART EVM Silent Launcher
' ============================================================
' Double-click this file to start the SMART EVM application
' WITHOUT any CMD / terminal window appearing.
'
' Windows runs .vbs files with wscript.exe which is completely
' silent - no black CMD box ever opens.
' ============================================================

Dim WshShell, strDir, strCmd

Set WshShell = CreateObject("WScript.Shell")

' Determine the folder where this script lives
strDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))

' Activate the virtual environment's pythonw (no console window)
' If .venv doesn't exist yet, fall back to system pythonw / python
Dim pyExe
If CreateObject("Scripting.FileSystemObject").FileExists(strDir & ".venv\Scripts\pythonw.exe") Then
    pyExe = """" & strDir & ".venv\Scripts\pythonw.exe"""
ElseIf CreateObject("Scripting.FileSystemObject").FileExists(strDir & ".venv\Scripts\python.exe") Then
    pyExe = """" & strDir & ".venv\Scripts\python.exe"""
Else
    pyExe = "pythonw"
End If

strCmd = pyExe & " """ & strDir & "main.py"""

' 0 = hidden window, False = don't wait for it to finish
WshShell.Run strCmd, 0, False

Set WshShell = Nothing
