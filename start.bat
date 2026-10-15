@echo off
title BNI Timesheet Automator
echo ===================================================
echo  Menjalankan BNI / MII Timesheet Automator Web App
echo ===================================================
echo.

if not exist config.json (
    if exist config.example.json (
        echo [INFO] Membuat config.json otomatis dari template config.example.json...
        copy config.example.json config.json >nul
        echo [INFO] Silakan sesuaikan nama dan NIK Anda di file config.json.
    )
)

timeout /t 2 >nul
start http://127.0.0.1:8000
python cli.py web
pause
