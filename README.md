This is an easy way to find plc's ip addresses trough nmap make sure you have nmap installed!

on ubuntu:
sudo snap install nmap

fedora:
sudo dnf install nmap

arch:
sudo pacman -S nmap

When you have installed just enter this prompt: nmap -p 102,502,44818 --open <"enter your ip range example: 192.168.0.0/24"> 
