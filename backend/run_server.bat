@echo off
cd /d "m:\DIU-WISE-AI\backend"

:: Add Miniconda DLL directories to PATH so numpy/sklearn load correctly
set PATH=M:\Miniconda\Library\bin;M:\Miniconda\Library\mingw-w64\bin;M:\Miniconda\Scripts;M:\Miniconda;%PATH%

:: Activate the venv
call .venv\Scripts\activate.bat

set PYTHONUNBUFFERED=1
echo [%TIME%] Starting server...
python -u start.py
pause
