@echo off
setlocal

REM Activate venv if present
if exist "%~dp0.venv\Scripts\activate.bat" call "%~dp0.venv\Scripts\activate.bat"

echo.
echo ===== Whisper Transcriber =====
echo.

REM ---- Accuracy / Model ----
echo Choose accuracy / speed level:
echo   1) fastest  (tiny)
echo   2) fast     (base)
echo   3) balanced (small)  [default]
echo   4) accurate (medium)
echo   5) best     (large-v3)
echo.
set "MODEL=small"
set /p ACC=Select 1-5 (default 3): 
if "%ACC%"=="1" set "MODEL=tiny"
if "%ACC%"=="2" set "MODEL=base"
if "%ACC%"=="3" set "MODEL=small"
if "%ACC%"=="4" set "MODEL=medium"
if "%ACC%"=="5" set "MODEL=large-v3"

echo.
REM ---- Output formats ----
echo Select output formats (you can choose multiple):
echo   1) TXT
echo   2) SRT
echo   3) VTT
echo Example: 1,2  or  1,3  or  1,2,3
echo.
set /p FMT=Your choice [default: 1]: 

set "OUTPUTS="
if "%FMT%"=="" (
  set "OUTPUTS=txt"
) else (
  echo %FMT%| findstr /C:"1" >nul && set "OUTPUTS=%OUTPUTS%txt,"
  echo %FMT%| findstr /C:"2" >nul && set "OUTPUTS=%OUTPUTS%srt,"
  echo %FMT%| findstr /C:"3" >nul && set "OUTPUTS=%OUTPUTS%vtt,"
  if "%OUTPUTS%"=="" set "OUTPUTS=txt"
  if not "%OUTPUTS%"=="" set "OUTPUTS=%OUTPUTS:~0,-1%"
)

echo.
REM ---- Input language ----
echo Select INPUT language (spoken in your media):
echo   1) English (en)
echo   2) Mandarin Chinese (zh)
echo   3) Hindi (hi)
echo   4) Spanish (es)
echo   5) Arabic (ar)
echo   6) Italian (it)
echo.
set "INLANG=it"
set /p INSEL=Select 1-6 [default 6=Italian]: 
if "%INSEL%"=="1" set "INLANG=en"
if "%INSEL%"=="2" set "INLANG=zh"
if "%INSEL%"=="3" set "INLANG=hi"
if "%INSEL%"=="4" set "INLANG=es"
if "%INSEL%"=="5" set "INLANG=ar"
if "%INSEL%"=="6" set "INLANG=it"

echo.
REM ---- Output language ----
echo Select OUTPUT language:
echo   1) English (en)
echo   2) Mandarin Chinese (zh)
echo   3) Hindi (hi)
echo   4) Spanish (es)
echo   5) Arabic (ar)
echo   6) Italian (it)
echo.
set "OUTLANG=it"
set /p OUTSEL=Select 1-6 [default 6=Italian]: 
if "%OUTSEL%"=="1" set "OUTLANG=en"
if "%OUTSEL%"=="2" set "OUTLANG=zh"
if "%OUTSEL%"=="3" set "OUTLANG=hi"
if "%OUTSEL%"=="4" set "OUTLANG=es"
if "%OUTSEL%"=="5" set "OUTLANG=ar"
if "%OUTSEL%"=="6" set "OUTLANG=it"

echo.
echo [INFO] Model:   %MODEL%
echo [INFO] Outputs: %OUTPUTS%
echo [INFO] InLang:  %INLANG%
echo [INFO] OutLang: %OUTLANG%
echo.

python "%~dp0transcribe.py" --model %MODEL% --outputs %OUTPUTS% --in-lang %INLANG% --out-lang %OUTLANG% %*

echo.
pause
