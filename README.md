# 🔍 nmaping-plc-s

A simple and fast tool to discover PLCs on your network using **nmap**.  
Scans for common industrial protocol ports like **Modbus (502)**, **EtherNet/IP (44818)**, and **port 102 (S7comm/ISO-TSAP)**.

---

## 📋 Requirements

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
## 🖥️ Script
Clone the repo and run:
```bash
chmod +x nmaping.sh
./nmaping.sh
```
## 🚀 Usage

Run the following command and replace the IP range with your own network:

```bash
nmap -p 102,502,44818 --open <your-ip-range>
```

**Example:**

```bash
nmap -p 102,502,44818 --open 192.168.0.0/24
```

This will scan your entire `192.168.0.x` subnet and show only devices with those ports open.

---

## 🔌 Scanned Ports

| Port | Protocol | Used by |
|------|----------|---------|
| 102 | S7comm / ISO-TSAP | Siemens S7 PLCs |
| 502 | Modbus TCP | Many PLCs & industrial devices |
| 44818 | EtherNet/IP | Allen-Bradley / Rockwell PLCs |

---

## 📌 Tips

- Run with `sudo` for faster and more accurate results:
  ```bash
  sudo nmap -p 102,502,44818 --open 192.168.0.0/24
  ```
- Add `-sV` to detect the service version running on open ports:
  ```bash
  sudo nmap -p 102,502,44818 -sV --open 192.168.0.0/24
  ```
- Not sure what your IP range is? Run `ip a` (Linux) or `ipconfig` (Windows).

---

## 📄 License

This project is licensed under the **GPL-3.0 License** — see the [LICENSE](LICENSE) file for details.

---

> Made by [jonasvo20-ux](https://github.com/jonasvo20-ux)
