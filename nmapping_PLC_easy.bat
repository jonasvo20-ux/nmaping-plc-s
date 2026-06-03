@echo off
title PLC Network Scanner - Easy Mode
color 0A

:: Check if nmap is installed
where nmap >nul 2>&1
if errorlevel 1 (
    cls
    echo ============================================
    echo  ERROR: nmap is not installed
    echo ============================================
    echo.
    echo  nmap is required to run this scanner.
    echo  A popup will open asking if you want to
    echo  go to the download page.
    echo.
    powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $r = [System.Windows.Forms.MessageBox]::Show('nmap is not installed on this machine.`n`nIt is required to scan for PLC devices.`n`nClick OK to open the download page in your browser, or Cancel to exit.', 'nmap Not Found', [System.Windows.Forms.MessageBoxButtons]::OKCancel, [System.Windows.Forms.MessageBoxIcon]::Warning); if ($r -eq 'OK') { Start-Process 'https://nmap.org/download.html' }"
    echo.
    echo  After installing nmap, re-run this script.
    echo.
    pause
    exit /b 1
)

:MENU
cls
echo ============================================
echo         PLC NETWORK SCANNER - EASY MODE
echo ============================================
echo.
echo  Scans for common PLC protocols:
echo    102   - S7comm  (Siemens PLCs)
echo    502   - Modbus  (Many PLC brands)
echo    44818 - EtherNet/IP (Allen-Bradley etc.)
echo.
echo ============================================
echo  SELECT YOUR IP RANGE:
echo ============================================
echo.
echo  [1] 192.168.0.0/24   (common home/office)
echo  [2] 192.168.1.0/24   (common home/office)
echo  [3] 10.0.0.0/24      (common industrial)
echo  [4] 10.10.0.0/24     (common industrial)
echo  [5] 172.16.0.0/24    (common industrial)
echo  [6] Enter custom range
echo  [7] Scan a single IP
echo  [Q] Quit
echo.
set /p choice="Select option: "

if /i "%choice%"=="1" set range=192.168.0.0/24 & goto PORTSCAN
if /i "%choice%"=="2" set range=192.168.1.0/24 & goto PORTSCAN
if /i "%choice%"=="3" set range=10.0.0.0/24 & goto PORTSCAN
if /i "%choice%"=="4" set range=10.10.0.0/24 & goto PORTSCAN
if /i "%choice%"=="5" set range=172.16.0.0/24 & goto PORTSCAN
if /i "%choice%"=="6" goto CUSTOM
if /i "%choice%"=="7" goto SINGLE
if /i "%choice%"=="Q" goto QUIT
echo Invalid option, try again.
timeout /t 1 >nul
goto MENU

:CUSTOM
cls
echo ============================================
echo  CUSTOM IP RANGE
echo ============================================
echo.
echo  Examples:
echo    192.168.0.0/24   (whole subnet)
echo    192.168.0.1-50   (range of IPs)
echo    10.0.0.0/16      (larger subnet)
echo.
set /p range="Enter IP range: "
if "%range%"=="" (
    echo No range entered, going back...
    timeout /t 2 >nul
    goto MENU
)
goto PORTSCAN

:SINGLE
cls
echo ============================================
echo  SINGLE IP SCAN
echo ============================================
echo.
set /p range="Enter IP address (e.g. 192.168.0.10): "
if "%range%"=="" (
    echo No IP entered, going back...
    timeout /t 2 >nul
    goto MENU
)
goto PORTSCAN

:PORTSCAN
cls
echo ============================================
echo  SCANNING: %range%
echo ============================================
echo.
echo  Looking for PLCs on ports 102, 502, 44818...
echo.

set /p savefile="Save results to file? (y/n): "
if /i "%savefile%"=="y" (
    set timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
    set timestamp=%timestamp: =0%
    set outfile=plc_scan_%timestamp%.txt
    echo Results will be saved to: %outfile%
    echo.
    nmap -p 102,502,44818 --open "%range%" -oN "%outfile%"
    echo.
    echo Results saved to: %outfile%
) else (
    nmap -p 102,502,44818 --open "%range%"
)

echo.
echo ============================================
echo  SCAN COMPLETE
echo ============================================
echo.
set /p again="Scan again? (y/n): "
if /i "%again%"=="y" goto MENU

:QUIT
echo.
echo Goodbye!
timeout /t 2 >nul
exit /b 0
