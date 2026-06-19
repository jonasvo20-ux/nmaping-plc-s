# PLC Network Scanner

> Industrial device discovery tool for OT/ICS networks.  
> Scans for PLCs and industrial devices by probing **S7/ISO-TSAP (102)**, **Modbus TCP (502)**, and **EtherNet/IP (44818)**.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-cyan)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-2.0.0-orange)

---

## What's New in v1.0.0 — Full GUI Release

The tool has been completely rebuilt from the ground up with a modern dark GUI.  
The old batch/shell scripts are still included for quick CLI use, but the GUI is now the main experience.

| Feature | Details |
|---|---|
| Fullscreen dark launcher | Splash screen with AUTO DETECT and MANUAL mode |
| Cross-platform fonts | Consolas / Menlo / DejaVu Sans Mono per OS |
| Input sanitization | Whitelist-only IP/CIDR validation — no injection possible |
| Rate limiting | `--max-rate 100 pps` — safe for fragile OT networks |
| Scope guardrail | Blocks ranges broader than /16 |
| Scan cooldown | 5 second enforced delay between scans |
| Auto-save | Every scan auto-saves a timestamped `.txt` to your results folder |
| Logging | Persistent `plc_scanner.log` with full audit trail |
| First-run setup | Asks where to store results on first launch, never again |
| nmap check | Detects missing nmap before scan starts, not mid-scan |

---

## Screenshots.

> _Coming soon — contributions welcome._

---

## Installation

### Linux (Debian / Ubuntu) — Recommended

Download the `.deb` from the [Releases](../../releases) page and install:

```bash
sudo dpkg -i plc-scanner_1.0.0_all.deb
sudo apt-get install -f    # installs any missing dependencies
```

Then launch from your app menu or run:

```bash
plc-scanner
```

To uninstall:

```bash
sudo dpkg -r plc-scanner
```

---

### Windows & macOS — Run from source

**1. Install Python 3.10+**  
Download from [python.org](https://python.org). On Windows, tick **"Add Python to PATH"** during install.

**2. Install dependencies**

```bash
pip install customtkinter
```

**3. Install nmap**

| OS | Command |
|----|---------|
| Ubuntu / Debian | `sudo apt install nmap` |
| Arch Linux | `sudo pacman -S nmap` |
| Fedora | `sudo dnf install nmap` |
| macOS | `brew install nmap` |
| Windows | [nmap.org/download.html](https://nmap.org/download.html) — tick "Add to PATH" |

**4. Run**

```bash
python plc_scanner.py
```

---

## CLI / Legacy Scripts.

The original bash and batch scripts are still included for headless or quick use:

| Script | Platform | Description |
|--------|----------|-------------|
| `nmapping.sh` | Linux / macOS | Bash script, prompts for IP range |
| `nmapping_PLC.bat` | Windows | Simple batch with nmap check |
| `nmapping_PLC_easy.bat` | Windows | Interactive menu, presets, save to file |

```bash
# Linux / macOS
chmod +x nmapping.sh && ./nmapping.sh

# Or run nmap directly
nmap -p 102,502,44818 --open 192.168.1.0/24
```

---

## Scanned Ports

| Port | Protocol | Devices |
|------|----------|---------|
| 102 | S7comm / ISO-TSAP | Siemens S7-1200, S7-300, S7-400 |
| 502 | Modbus TCP | Most PLCs, VFDs, meters, sensors |
| 44818 | EtherNet/IP | Allen-Bradley / Rockwell, Omron |

---

## Security & Responsible Use

- **Only scan networks you own or have explicit written permission to scan.**
- Unauthorized network scanning may be illegal in your jurisdiction.
- The tool enforces a /16 maximum scan range and 100 pps rate limit to protect sensitive OT environments.
- Results and logs may contain sensitive network topology data — store them securely.

---

## Requirements

- Python 3.10+
- nmap (on system PATH)
- `customtkinter` Python package
- Linux: `python3-tk`, `fonts-dejavu-core`

---

## License

MIT License — see [LICENSE](LICENSE) for details.  
Free to use, modify, and distribute. Attribution appreciated.

---

## Support

If this tool saved you time, a coffee goes a long way. ☕

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-jonasvo20-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/jonasvo20)

---

> Made by [jonasvo20-ux](https://github.com/jonasvo20-ux) · Built with Python & CustomTkinter · Powered by nmap
