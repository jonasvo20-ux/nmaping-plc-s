# nmaping-plc-s

A fast and easy tool to discover PLCs on your network using **nmap**.  
Scans for common industrial protocol ports: **Modbus (502)**, **EtherNet/IP (44818)**, and **S7comm/ISO-TSAP (102)**.

---

## MASSIVE UPDATE — Full Cross-Platform Support

nmaping-plc-s now runs on **Linux, macOS, and Windows** with dedicated scripts for each platform.  
No more manual command typing — just run the script for your OS and go.

| Platform | Script | Description |
|----------|--------|-------------|
| Linux / macOS | `nmapping.sh` | Bash script, prompts for IP range and scans |
| Windows | `nmapping_PLC.bat` | Simple batch script with nmap check |
| Windows (Easy Mode) | `nmapping_PLC_easy.bat` | Interactive menu with preset ranges, single IP mode, and save-to-file |

---

## Requirements

- [nmap](https://nmap.org/) installed on your system

### Install nmap

| OS | Command |
|----|---------|
| Ubuntu / Debian | `sudo apt install nmap` |
| Fedora | `sudo dnf install nmap` |
| Arch Linux | `sudo pacman -S nmap` |
| macOS | `brew install nmap` |
| Windows | [Download installer](https://nmap.org/download.html) |

---

## Usage

### Linux / macOS

```bash
chmod +x nmapping.sh
./nmapping.sh
```

The script will prompt you to enter your IP range and run the scan automatically.

### Windows — Standard

Double-click `nmapping_PLC.bat` or run it from a terminal:

```cmd
nmapping_PLC.bat
```

If nmap is not installed, a popup will open and offer to take you to the download page.

### Windows — Easy Mode

Double-click `nmapping_PLC_easy.bat` or run it from a terminal:

```cmd
nmapping_PLC_easy.bat
```

Features:
- Interactive menu with common preset IP ranges (home/office and industrial)
- Option to enter a custom range or scan a single IP
- Option to save scan results to a timestamped `.txt` file
- Scan again without restarting

---

## Manual Usage

You can also run nmap directly without any script:

```bash
nmap -p 102,502,44818 --open <your-ip-range>
```

**Example:**

```bash
nmap -p 102,502,44818 --open 192.168.0.0/24
```

---

## Scanned Ports

| Port | Protocol | Used by |
|------|----------|---------|
| 102 | S7comm / ISO-TSAP | Siemens S7 PLCs |
| 502 | Modbus TCP | Many PLCs & industrial devices |
| 44818 | EtherNet/IP | Allen-Bradley / Rockwell PLCs |

---

## Tips

- Run with `sudo` on Linux/macOS for faster and more accurate results:
  ```bash
  sudo nmap -p 102,502,44818 --open 192.168.0.0/24
  ```
- Add `-sV` to detect service versions on open ports:
  ```bash
  sudo nmap -p 102,502,44818 -sV --open 192.168.0.0/24
  ```
- Not sure what your IP range is? Run `ip a` (Linux/macOS) or `ipconfig` (Windows).

---

## License

This project is licensed under the **GPL-3.0 License** — see the [LICENSE](LICENSE) file for details.

---

> Made by [jonasvo20-ux](https://github.com/jonasvo20-ux)
