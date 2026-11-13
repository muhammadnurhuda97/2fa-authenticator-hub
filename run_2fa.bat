@echo off
chcp 65001 >nul
title 2FA Authenticator Hub (Sinkron 2fa.cn)

echo ========================================================
echo   2FA Authenticator Hub (RFC 6238 / 2fa.cn)
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/2] Menyiapkan server lokal...
start "" http://127.0.0.1:8799

echo [2/2] Membuka dashboard 2FA di browser: http://127.0.0.1:8799
echo.
echo Tekan CTRL + C untuk menutup server.
echo.

python server.py
pause
