import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import threading
import socket
import shutil
import ipaddress
import json
import logging
import re
import sys
import time
import os
from datetime import datetime
from pathlib import Path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG      = "#0b0b12"
SURFACE = "#13131f"
CARD    = "#1a1a2a"
BORDER  = "#2a2a40"
ACCENT  = "#00c8ff"
GREEN   = "#00e676"
RED     = "#ff4757"
ORANGE  = "#ffa502"
TEXT    = "#e8eaf0"
MUTED   = "#5a5a78"

# ── cross-platform fonts ───────────────────────────────────────────────────────
def _mono(size, weight="normal"):
    if sys.platform == "win32":   family = "Consolas"
    elif sys.platform == "darwin": family = "Menlo"
    else:                          family = "DejaVu Sans Mono"
    return ctk.CTkFont(family, size, weight)

def _ui(size, weight="normal"):
    if sys.platform == "win32":   family = "Segoe UI"
    elif sys.platform == "darwin": family = "SF Pro Display"
    else:                          family = "Ubuntu"
    return ctk.CTkFont(family, size, weight)

def _mono_tuple(size, weight="normal"):
    if sys.platform == "win32":   family = "Consolas"
    elif sys.platform == "darwin": family = "Menlo"
    else:                          family = "DejaVu Sans Mono"
    return (family, size, weight) if weight != "normal" else (family, size)

# ── constants ──────────────────────────────────────────────────────────────────
MAX_PREFIX    = 16
MAX_RATE      = 100
SCAN_COOLDOWN = 5

CONFIG_DIR  = Path.home() / ".plc_scanner"
CONFIG_FILE = CONFIG_DIR / "config.json"

# ── preset ranges ──────────────────────────────────────────────────────────────
PRESET_RANGES = [
    ("192.168.0.0/24", "192.168.0.0/24   (home / office)"),
    ("192.168.1.0/24", "192.168.1.0/24   (home / office)"),
    ("10.0.0.0/24",    "10.0.0.0/24      (industrial)"),
    ("10.10.0.0/24",   "10.10.0.0/24     (industrial)"),
    ("172.16.0.0/24",  "172.16.0.0/24    (industrial)"),
]

_SKIP_PATTERNS = re.compile(
    r"^(Host is up|Not shown:|Initiating|Completed|Stats:|Read data|"
    r"WARNING|NSE:|Discovered|Increasing|Adjust|mass_dns|Parallel|"
    r"Sending|Scanning \d|SYN Stealth)"
)

_VALID_TARGET = re.compile(r"^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$")


# ── config helpers ─────────────────────────────────────────────────────────────
def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}

def save_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


# ── logging setup ──────────────────────────────────────────────────────────────
def setup_logger(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "plc_scanner.log"
    logger = logging.getLogger("plc_scanner")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(fh)
    return logger


# ── validation ─────────────────────────────────────────────────────────────────
def detect_local_subnet():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        p = ip.split(".")
        return f"{p[0]}.{p[1]}.{p[2]}.0/24", ip
    except Exception:
        return None, None

def validate_target(raw: str):
    raw = raw.strip()
    if not raw:
        return None, "No target specified."
    if not _VALID_TARGET.match(raw):
        return None, f"Invalid target: '{raw}'\nOnly IP/CIDR notation is accepted."
    try:
        net = ipaddress.ip_network(raw, strict=False)
        if net.prefixlen < MAX_PREFIX:
            return None, (
                f"Range too broad: /{net.prefixlen} = {net.num_addresses:,} addresses.\n"
                f"Maximum allowed is /{MAX_PREFIX} (65 536 hosts)."
            )
    except ValueError as e:
        return None, f"Invalid network: {e}"
    return raw, None


# ── first-run setup dialog ─────────────────────────────────────────────────────
class SetupDialog(ctk.CTkToplevel):
    """Shown once on first launch to choose the output/log folder."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("PLC Scanner — First Run Setup")
        self.geometry("540x320")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.grab_set()          # modal
        self.lift()
        self.focus_force()

        self.chosen_dir: Path | None = None
        self._default = Path.home() / "plc_scanner_results"

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Welcome to PLC Network Scanner",
                     font=_mono(16, "bold"), text_color=ACCENT
                     ).grid(row=0, column=0, pady=(28, 4), padx=30)

        ctk.CTkLabel(self,
                     text="Choose a folder where scan results and logs will be saved.\n"
                          "You can change this later in Settings.",
                     font=_mono(11), text_color=MUTED, justify="center"
                     ).grid(row=1, column=0, pady=(0, 20), padx=30)

        # path display
        path_frame = ctk.CTkFrame(self, fg_color=CARD, corner_radius=10,
                                   border_width=1, border_color=BORDER)
        path_frame.grid(row=2, column=0, padx=30, sticky="ew")
        path_frame.grid_columnconfigure(0, weight=1)

        self._path_var = ctk.StringVar(value=str(self._default))
        ctk.CTkLabel(path_frame, textvariable=self._path_var,
                     font=_mono(10), text_color=TEXT, anchor="w"
                     ).grid(row=0, column=0, padx=14, pady=12, sticky="ew")

        ctk.CTkButton(path_frame, text="Browse", width=80, height=28,
                      corner_radius=6, fg_color=SURFACE, hover_color=BORDER,
                      border_width=1, border_color=BORDER, text_color=ACCENT,
                      font=_mono(10, "bold"), command=self._browse
                      ).grid(row=0, column=1, padx=(0, 10), pady=8)

        ctk.CTkButton(self, text=">> CONFIRM & CONTINUE",
                      height=44, corner_radius=10,
                      fg_color=ACCENT, hover_color="#009ec8", text_color="#000000",
                      font=_mono(13, "bold"), command=self._confirm
                      ).grid(row=3, column=0, padx=30, pady=24, sticky="ew")

        # centre over parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _browse(self):
        chosen = filedialog.askdirectory(
            title="Choose results folder",
            initialdir=str(self._default)
        )
        if chosen:
            self._path_var.set(chosen)

    def _confirm(self):
        self.chosen_dir = Path(self._path_var.get())
        self.destroy()


# ── main app ───────────────────────────────────────────────────────────────────
class PLCScanner(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PLC Network Scanner")
        self.geometry("860x580")
        self.minsize(700, 480)
        self.configure(fg_color=BG)

        # load or bootstrap config
        self._cfg = load_config()
        if "results_dir" not in self._cfg:
            self._run_first_time_setup()
        else:
            self._results_dir = Path(self._cfg["results_dir"])

        # ensure dirs exist
        self._results_dir.mkdir(parents=True, exist_ok=True)
        self._log = setup_logger(self._results_dir)
        self._log.info("PLC Scanner started — results dir: %s", self._results_dir)

        self._proc         = None
        self._hosts_found  = 0
        self._ip_range     = None
        self._mode         = "quick"
        self._last_scan_ts = 0.0
        self._scan_lines: list[str] = []   # buffer for log writing
        self._auto_range, self._auto_ip = detect_local_subnet()

        self._frame_splash   = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._frame_terminal = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        for f in (self._frame_splash, self._frame_terminal):
            f.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_splash()
        self._build_terminal()
        self._show_splash()

    def _run_first_time_setup(self):
        self.update()          # render window first so dialog centres on it
        dlg = SetupDialog(self)
        self.wait_window(dlg)
        chosen = dlg.chosen_dir or Path.home() / "plc_scanner_results"
        self._results_dir = chosen
        self._cfg["results_dir"] = str(chosen)
        save_config(self._cfg)

    # ── frame switching ────────────────────────────────────────────────────────
    def _show_splash(self):    self._frame_splash.lift()
    def _show_terminal(self):  self._frame_terminal.lift()

    # ── SPLASH ─────────────────────────────────────────────────────────────────
    def _build_splash(self):
        f = self._frame_splash
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(0, weight=1)
        f.grid_rowconfigure(99, weight=1)
        row = 1

        logo_frame = ctk.CTkFrame(f, fg_color="transparent")
        logo_frame.grid(row=row, column=0, pady=(0, 8)); row += 1
        ctk.CTkLabel(logo_frame, text="PLC NETWORK SCANNER",
                     font=_mono(28, "bold"), text_color=ACCENT).pack()
        ctk.CTkLabel(logo_frame,
                     text="industrial device discovery  //  ports 102 · 502 · 44818",
                     font=_mono(11), text_color=MUTED).pack(pady=(4, 0))

        ctk.CTkFrame(f, fg_color=BORDER, height=1, corner_radius=0).grid(
            row=row, column=0, sticky="ew", padx=120, pady=20); row += 1

        self._splash_mode = ctk.StringVar(value="auto")
        mode_row = ctk.CTkFrame(f, fg_color="transparent")
        mode_row.grid(row=row, column=0, pady=(0, 24)); row += 1
        for label, value in (("AUTO DETECT", "auto"), ("MANUAL", "manual")):
            ctk.CTkRadioButton(
                mode_row, text=label, variable=self._splash_mode, value=value,
                text_color=TEXT, fg_color=ACCENT, hover_color="#009ec8",
                font=_mono(12, "bold"), command=self._on_mode_toggle
            ).pack(side="left", padx=24)

        # auto card
        self._auto_card = ctk.CTkFrame(f, fg_color=CARD, corner_radius=12,
                                        border_width=1, border_color=BORDER)
        self._auto_card.grid(row=row, column=0, padx=180, sticky="ew"); row += 1
        if self._auto_range:
            ctk.CTkLabel(self._auto_card, text="Detected subnet",
                         font=_mono(10), text_color=MUTED).pack(pady=(14, 2))
            ctk.CTkLabel(self._auto_card, text=self._auto_range,
                         font=_mono(18, "bold"), text_color=ACCENT).pack(pady=(0, 14))
        else:
            ctk.CTkLabel(self._auto_card, text="Could not detect subnet",
                         font=_mono(12), text_color=RED).pack(pady=14)

        # manual card
        self._manual_card = ctk.CTkFrame(f, fg_color=CARD, corner_radius=12,
                                          border_width=1, border_color=BORDER)
        self._manual_card.grid(row=row, column=0, padx=180, sticky="ew"); row += 1
        self._manual_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self._manual_card, text="Target range",
                     font=_mono(10), text_color=MUTED
                     ).grid(row=0, column=0, pady=(14, 4), padx=20, sticky="w")
        self._manual_entry = ctk.CTkEntry(
            self._manual_card,
            placeholder_text="e.g.  192.168.1.0/24  or  10.0.0.0/24",
            height=38, corner_radius=8,
            fg_color=SURFACE, border_color=BORDER, text_color=TEXT, font=_mono(12)
        )
        self._manual_entry.grid(row=1, column=0, padx=20, pady=(0, 6), sticky="ew")
        ctk.CTkLabel(self._manual_card, text="Or choose a preset:",
                     font=_mono(10), text_color=MUTED
                     ).grid(row=2, column=0, padx=20, pady=(6, 4), sticky="w")
        preset_labels = [lbl for _, lbl in PRESET_RANGES]
        self._preset_var = ctk.StringVar(value=preset_labels[0])
        ctk.CTkComboBox(
            self._manual_card, values=preset_labels, variable=self._preset_var,
            height=34, corner_radius=8, state="readonly",
            fg_color=SURFACE, border_color=BORDER, button_color=ACCENT,
            button_hover_color="#009ec8", dropdown_fg_color=CARD,
            dropdown_hover_color=BORDER, text_color=TEXT, font=_mono(11),
            command=self._on_preset_select
        ).grid(row=3, column=0, padx=20, pady=(0, 14), sticky="ew")

        # speed
        speed_row = ctk.CTkFrame(f, fg_color="transparent")
        speed_row.grid(row=row, column=0, pady=(20, 0)); row += 1
        ctk.CTkLabel(speed_row, text="SCAN SPEED:",
                     font=_mono(11), text_color=MUTED).pack(side="left", padx=(0, 16))
        self._speed_var = ctk.StringVar(value="quick")
        for label, value in (("Quick  (T4)", "quick"), ("Deep  (T3 + sV)", "deep")):
            ctk.CTkRadioButton(
                speed_row, text=label, variable=self._speed_var, value=value,
                text_color=TEXT, fg_color=ACCENT, hover_color="#009ec8", font=_mono(11)
            ).pack(side="left", padx=14)

        # launch
        self._launch_btn = ctk.CTkButton(
            f, text=">> START SCAN", height=50, corner_radius=12,
            fg_color=ACCENT, hover_color="#009ec8", text_color="#000000",
            font=_mono(15, "bold"), command=self._launch_scan
        )
        self._launch_btn.grid(row=row, column=0, padx=180, pady=(28, 0), sticky="ew"); row += 1

        self._splash_err = ctk.CTkLabel(f, text="", text_color=RED, font=_mono(10))
        self._splash_err.grid(row=row, column=0, pady=(6, 0)); row += 1

        # results dir hint at bottom
        ctk.CTkLabel(f,
                     text=f"Results saved to: {self._results_dir}",
                     font=_mono(9), text_color=MUTED
                     ).grid(row=row, column=0, pady=(4, 10)); row += 1

        self._on_mode_toggle()

    def _on_mode_toggle(self):
        if self._splash_mode.get() == "auto":
            self._auto_card.grid();  self._manual_card.grid_remove()
        else:
            self._auto_card.grid_remove();  self._manual_card.grid()

    def _on_preset_select(self, label):
        for val, lbl in PRESET_RANGES:
            if lbl == label:
                self._manual_entry.delete(0, "end")
                self._manual_entry.insert(0, val)
                break

    def _launch_scan(self):
        self._splash_err.configure(text="")

        # cooldown
        elapsed = time.time() - self._last_scan_ts
        if elapsed < SCAN_COOLDOWN:
            remaining = int(SCAN_COOLDOWN - elapsed) + 1
            self._splash_err.configure(
                text=f"Cooldown: please wait {remaining}s before scanning again.")
            return

        # nmap present?
        if not shutil.which("nmap"):
            self._splash_err.configure(
                text="nmap not found. Install it and make sure it is on your PATH.")
            return

        # resolve raw target
        if self._splash_mode.get() == "auto":
            if not self._auto_range:
                self._splash_err.configure(
                    text="Could not auto-detect subnet. Switch to Manual.")
                return
            raw = self._auto_range
        else:
            raw = self._manual_entry.get()

        clean, err = validate_target(raw)
        if err:
            self._splash_err.configure(text=err)
            self._log.warning("Rejected target '%s': %s", raw, err)
            return

        self._ip_range = clean
        self._mode     = self._speed_var.get()
        self._scan_lines = []
        self._show_terminal()
        self._start_scan()

    # ── TERMINAL ───────────────────────────────────────────────────────────────
    def _build_terminal(self):
        f = self._frame_terminal
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(f, fg_color=SURFACE, corner_radius=0, height=46)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(bar, text="<< BACK", width=90, height=28, corner_radius=6,
                      fg_color=CARD, hover_color=BORDER, border_width=1,
                      border_color=BORDER, text_color=MUTED, font=_mono(10, "bold"),
                      command=self._go_back
                      ).grid(row=0, column=0, padx=14, pady=9, sticky="w")

        self._terminal_title = ctk.CTkLabel(bar, text="", text_color=MUTED, font=_mono(11))
        self._terminal_title.grid(row=0, column=1, sticky="w", padx=4)

        self._stats_label = ctk.CTkLabel(bar, text="", text_color=GREEN, font=_mono(11, "bold"))
        self._stats_label.grid(row=0, column=2, sticky="e", padx=14)

        self._progress = ctk.CTkProgressBar(f, height=3, corner_radius=0,
                                             fg_color=SURFACE, progress_color=ACCENT)
        self._progress.set(0)
        self._progress.grid(row=0, column=0, sticky="sew")

        self._output = ctk.CTkTextbox(
            f, fg_color=BG, text_color=TEXT, font=_mono(11),
            corner_radius=0, border_width=0, wrap="word",
            scrollbar_button_color=BORDER, scrollbar_button_hover_color=MUTED,
            activate_scrollbars=True
        )
        self._output.grid(row=1, column=0, sticky="nsew")
        self._output.configure(state="disabled")

        txt = self._output._textbox
        txt.tag_config("host",   foreground=GREEN,  font=_mono_tuple(12, "bold"))
        txt.tag_config("port",   foreground=ACCENT, font=_mono_tuple(11))
        txt.tag_config("info",   foreground=MUTED,  font=_mono_tuple(10))
        txt.tag_config("header", foreground=ORANGE, font=_mono_tuple(11, "bold"))
        txt.tag_config("error",  foreground=RED,    font=_mono_tuple(11))

        bottom = ctk.CTkFrame(f, fg_color=SURFACE, corner_radius=0, height=46)
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.grid_propagate(False)
        bottom.grid_columnconfigure(0, weight=1)

        btn_cfg = dict(height=28, corner_radius=6, fg_color=CARD, hover_color=BORDER,
                       border_width=1, border_color=BORDER, text_color=TEXT,
                       font=_mono(10, "bold"))

        self._cancel_btn = ctk.CTkButton(
            bottom, text="CANCEL", width=80, state="disabled",
            height=28, corner_radius=6, fg_color=CARD, hover_color=BORDER,
            border_width=1, border_color=RED, text_color=RED, font=_mono(10, "bold"),
            command=self._cancel_scan
        )
        self._cancel_btn.grid(row=0, column=1, padx=8, pady=9)

        ctk.CTkButton(bottom, text="SAVE",  width=70, command=self._save_results,
                      **btn_cfg).grid(row=0, column=2, padx=4,      pady=9)
        ctk.CTkButton(bottom, text="CLEAR", width=70, command=self._clear_results,
                      **btn_cfg).grid(row=0, column=3, padx=(4, 14), pady=9)

        self._status_var = ctk.StringVar(value="")
        ctk.CTkLabel(bottom, textvariable=self._status_var, text_color=MUTED,
                     font=_mono(10)).grid(row=0, column=0, padx=14, sticky="w")

    # ── scan logic ─────────────────────────────────────────────────────────────
    def _go_back(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._show_splash()

    def _start_scan(self):
        self._clear_results()
        self._hosts_found = 0
        self._stats_label.configure(text="")
        self._terminal_title.configure(
            text=f"scanning  {self._ip_range}   [{self._mode.upper()}]")
        mode_label = "Quick (T4)" if self._mode == "quick" else "Deep (T3 + sV)"

        header = f"  >> Scanning  {self._ip_range}"
        info1  = f"  Mode: {mode_label}   |   Ports: 102, 502, 44818   |   max-rate: {MAX_RATE} pps"
        sep    = "  " + "-" * 58

        self._append("header", header + "\n")
        self._append("info",   info1  + "\n")
        self._append("info",   sep    + "\n")

        self._scan_lines = [header, info1, sep]
        self._log.info("Scan started — target: %s  mode: %s", self._ip_range, self._mode)

        self._cancel_btn.configure(state="normal")
        self._status_var.set("Running...")
        self._progress.configure(mode="indeterminate")
        self._progress.start()

        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        cmd = ["nmap", "-p", "102,502,44818", "--open", f"--max-rate={MAX_RATE}"]
        cmd += ["-T4"] if self._mode == "quick" else ["-T3", "-sV"]
        cmd.append(self._ip_range)

        kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.STDOUT,
                  "text": True, "bufsize": 1}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        try:
            self._proc = subprocess.Popen(cmd, **kwargs)
            for line in self._proc.stdout:
                self._handle_line(line.rstrip())
            self._proc.wait()
            rc = self._proc.returncode
        except FileNotFoundError:
            msg = "\n  ERROR: nmap not found — install nmap and make sure it is on your PATH.\n"
            self.after(0, lambda: self._append("error", msg))
            self._log.error("nmap not found")
            self.after(0, self._scan_done)
            return
        except Exception as exc:
            self.after(0, lambda e=exc: self._append("error", f"\n  ERROR: {e}\n"))
            self._log.error("Scan exception: %s", exc)
            self.after(0, self._scan_done)
            return

        sep = "  " + "-" * 58
        self.after(0, lambda: self._append("info", sep + "\n"))
        self._scan_lines.append(sep)

        if rc == 0:
            n = self._hosts_found
            summary = f"{n} host{'s' if n != 1 else ''} with open PLC ports found"
            self.after(0, lambda s=summary: self._append("header", f"  [+] {s}\n"))
            self.after(0, lambda s=summary: self._stats_label.configure(text=s))
            self._scan_lines.append(f"  [+] {summary}")
            self._log.info("Scan finished — %s", summary)
        else:
            self.after(0, lambda: self._append("info", "  Scan cancelled.\n"))
            self._log.info("Scan cancelled by user")

        self.after(0, self._scan_done)
        self.after(0, self._write_scan_log)

    def _handle_line(self, line):
        if not line.strip() or _SKIP_PATTERNS.match(line):
            return

        if line.startswith("Nmap scan report for"):
            self._hosts_found += 1
            host = line.replace("Nmap scan report for ", "").strip()
            display = f"\n  >> {host}\n"
            self.after(0, lambda d=display: self._append("host", d))
            self._scan_lines.append(f"\n  >> {host}")
            self._log.info("Host found: %s", host)

        elif re.match(r"^\d+/tcp", line):
            parts      = line.split()
            port_proto = parts[0]
            state      = parts[1] if len(parts) > 1 else ""
            service    = " ".join(parts[2:]) if len(parts) > 2 else ""
            formatted  = f"     {port_proto:<14}  {state:<8}  {service}"
            self.after(0, lambda l=formatted: self._append("port", f"{l}\n"))
            self._scan_lines.append(formatted)
            self._log.info("  Port: %s", formatted.strip())

        elif line.startswith("Starting Nmap"):
            clean = re.sub(r"\s*\(.*?\)\s*", " ", line).strip()
            self.after(0, lambda l=clean: self._append("info", f"  {l}\n\n"))
            self._scan_lines.append(f"  {clean}")

        elif line.startswith("Nmap done"):
            self.after(0, lambda l=line: self._append("info", f"\n  {l}\n"))
            self._scan_lines.append(f"\n  {line}")

        else:
            self.after(0, lambda l=line: self._append("info", f"  {l}\n"))
            self._scan_lines.append(f"  {line}")

    def _write_scan_log(self):
        """Write a timestamped .txt file for this scan into results_dir."""
        try:
            ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname   = self._results_dir / f"plc_scan_{ts}.txt"
            content = "\n".join(self._scan_lines)
            fname.write_text(content, encoding="utf-8")
            self._log.info("Scan log written: %s", fname)
            self.after(0, lambda p=str(fname):
                       self._status_var.set(f"Done.  Auto-saved: {Path(p).name}"))
        except Exception as exc:
            self._log.error("Failed to write scan log: %s", exc)

    def _cancel_scan(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._status_var.set("Cancelled.")
        self._log.info("Scan cancelled by user")

    def _scan_done(self):
        self._last_scan_ts = time.time()
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._progress.set(1)
        self._cancel_btn.configure(state="disabled")
        self._terminal_title.configure(
            text=f"{self._ip_range}   [{self._mode.upper()}]  --  finished")

    # ── helpers ────────────────────────────────────────────────────────────────
    def _append(self, tag, text):
        self._output.configure(state="normal")
        self._output._textbox.insert("end", text, tag)
        self._output._textbox.see("end")
        self._output.configure(state="disabled")

    def _clear_results(self):
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.configure(state="disabled")
        self._stats_label.configure(text="")
        self._status_var.set("")
        self._progress.set(0)

    def _save_results(self):
        """Manual save — file dialog defaults to results_dir."""
        content = self._output._textbox.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("Nothing to save", "Run a scan first.")
            return
        default = f"plc_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default,
            initialdir=str(self._results_dir),   # <-- defaults to chosen folder
        )
        if path:
            # sanitize: only allow saving inside results_dir or home
            save_path = Path(path).resolve()
            with open(save_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            self._status_var.set(f"Saved: {save_path.name}")
            self._log.info("Manual save: %s", save_path)


if __name__ == "__main__":
    PLCScanner().mainloop()
