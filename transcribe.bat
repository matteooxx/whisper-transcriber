@echo off
setlocal
if exist "%~dp0.venv\Scripts\activate.bat" call "%~dp0.venv\Scripts\activate.bat"
python "%~dp0transcribe.py" %*
echo.
pause
