#!/bin/bash
echo "=== PLC Network Scanner ==="

if ! command -v nmap &>/dev/null; then
    echo "Error: nmap is not installed."
    echo "  Debian/Ubuntu:  sudo apt install nmap"
    echo "  Fedora:         sudo dnf install nmap"
    echo "  Arch:           sudo pacman -S nmap"
    echo "  macOS:          brew install nmap"
    exit 1
fi

read -p "Enter your IP range (e.g. 192.168.0.0/24): " range
if [ -z "$range" ]; then
    echo "Error: IP range cannot be empty."
    exit 1
fi

read -p "Save results to file? (y/n): " savefile
echo "Scanning $range ..."
if [[ "$savefile" =~ ^[Yy]$ ]]; then
    timestamp=$(date +"%Y%m%d_%H%M%S")
    outfile="plc_scan_${timestamp}.txt"
    sudo nmap -p 102,502,44818 --open "$range" -oN "$outfile"
    echo "Results saved to: $outfile"
else
    sudo nmap -p 102,502,44818 --open "$range"
fi
