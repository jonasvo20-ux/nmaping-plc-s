#!/bin/bash
echo "=== PLC Network Scanner ==="
read -p "Enter your IP range (e.g. 192.168.0.0/24): " range
echo "Scanning $range ..."
sudo nmap -p 102,502,44818 --open "$range"
