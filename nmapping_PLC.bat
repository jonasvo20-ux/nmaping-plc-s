@echo off
title PLC Network Scanner

:: Check if nmap is installed
where nmap >nul 2>&1
if errorlevel 1 (
    echo nmap is not installed.
    powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $r = [System.Windows.Forms.MessageBox]::Show('nmap is not installed on this machine.`n`nClick OK to open the download page in your browser, or Cancel to exit.', 'nmap Not Found', [System.Windows.Forms.MessageBoxButtons]::OKCancel, [System.Windows.Forms.MessageBoxIcon]::Warning); if ($r -eq 'OK') { Start-Process 'https://nmap.org/download.html' }"
    exit /b 1
)

echo === PLC Network Scanner ===
echo Ports: 102 (S7/Siemens), 502 (Modbus), 44818 (EtherNet/IP)
echo.
set /p range="Enter your IP range (e.g. 192.168.0.0/24): "
if "%range%"=="" (
    echo Error: IP range cannot be empty.
    pause
    exit /b 1
)
echo.
echo Scanning %range% ...
echo.
nmap -p 102,502,44818 --open %range%
echo.
pause
