@echo off
title DIU WISE AI Server
color 0A
cd /d "m:\DIU-WISE-AI\backend"

echo ============================================
echo   DIU WISE AI - Starting Server
echo ============================================
echo.
echo  Killing any old Python processes...
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 >nul

echo  Loading AI models (please wait 5-10 min)...
echo  DO NOT CLOSE THIS WINDOW
echo.

set PYTHONUNBUFFERED=1
.venv\Scripts\python.exe app.py

echo.
echo Server stopped. Press any key to exit.
pause >nul
