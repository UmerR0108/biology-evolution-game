@echo off
setlocal
cd /d "%~dp0"

echo Starting AP Biology Evolution Game...

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -m pip install -e .
    py -3 scripts\run_game.py
    goto :done
)

where python >nul 2>nul
if %errorlevel%==0 (
    python -m pip install -e .
    python scripts\run_game.py
    goto :done
)

echo.
echo Python was not found. Please install Python 3.11 or newer from:
echo https://www.python.org/downloads/
echo Then run this file again.
pause
exit /b 1

:done
if errorlevel 1 (
    echo.
    echo The game exited with an error. If this is a school computer, try the web backup link in README_TEACHER.txt.
    pause
)
