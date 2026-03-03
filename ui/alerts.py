"""
ui/alerts.py — Alert settings panel + notification dispatcher.

AlertSettings  : a tk.Toplevel dialog to configure thresholds.
AlertManager   : evaluates data and fires desktop notifications.
AlertBanner    : an inline banner shown at the top of the dashboard.
"""

import tkinter as tk
from tkinter import ttk
import platform
import subprocess
import threading

import config
import data as datalib


# ── Desktop notification helper ──────────────────────────────────────────────

def _notify(title: str, message: str, urgency: str = "normal"):
    """
    Best-effort desktop notification.
    Works on macOS, Linux (notify-send), and Windows (basic messagebox fallback).
    Runs in a background thread so it never blocks the UI.
    """
    def _send():
        system = platform.system()
        try:
            if system == "Darwin":
                script = (
                    f'display notification "{message}" '
                    f'with title "{title}" '
                    f'sound name "Basso"'
                )
                subprocess.run(["osascript", "-e", script],
                               capture_output=True, timeout=5)
            elif system == "Linux":
                level = "critical" if urgency == "urgent" else "normal"
                subprocess.run(
                    ["notify-send", "-u", level, title, message],
                    capture_output=True, timeout=5
                )
            elif system == "Windows":
                # Requires win10toast: pip install win10toast
                try:
                    from win10toast import ToastNotifier
                    ToastNotifier().show_toast(title, message, duration=6,
                                              threaded=True)
                except ImportError:
                    pass  # silently skip if not installed
        except Exception:
            pass  # notifications are best-effort, never crash the app

    threading.Thread(target=_send, daemon=True).start()


# ── Alert Manager ─────────────────────────────────────────────────────────────

class AlertManager:
    """
    Compares current glucose data against thresholds and fires notifications.
    Tracks which alerts have already fired to avoid repeated pings.
    """

    def __init__(self):
        self.settings = {
            "alerts_enabled":  True,
            "alert_low":       config.ALERT_LOW_DEFAULT,
            "alert_high":      config.ALERT_HIGH_DEFAULT,
            "rapid_rise_rate": config.ALERT_RAPID_RISE_RATE,
            "rapid_fall_rate": config.ALERT_RAPID_FALL_RATE,
        }
        self._fired: set = set()   # tracks alert keys already notified

    def evaluate(self, values: list, times: list) -> list[dict]:
        """
        Check for active alerts. Fires a desktop notification for any new ones.
        Returns full list of currently active alerts.
        """
        active = datalib.check_alerts(values, times, self.settings)

        for alert in active:
            key = (alert["level"], alert["message"])
            if key not in self._fired:
                self._fired.add(key)
                title = {
                    "urgent":  "🚨 Urgent Glucose Alert",
                    "low":     "⬇️  Low Glucose",
                    "high":    "⬆️  High Glucose",
                    "warning": "⚠️  Glucose Warning",
                }.get(alert["level"], "Glucose Alert")
                _notify(title, alert["message"], urgency=alert["level"])

        # Clear fired cache for alerts that are no longer active
        active_keys = {(a["level"], a["message"]) for a in active}
        self._fired &= active_keys

        return active

    def update_settings(self, new_settings: dict):
        self.settings.update(new_settings)
        self._fired.clear()   # reset so re-evaluated with new thresholds


# ── Alert Banner (inline UI) ──────────────────────────────────────────────────

class AlertBanner(tk.Frame):
    """
    A slim banner displayed at the top of the dashboard when alerts are active.
    Hidden when there are no alerts.
    """

    def __init__(self, parent):
        super().__init__(parent, bg=config.COLOR_BG)
        self._label = tk.Label(self, text="", font=config.FONT_BODY,
                               bg=config.COLOR_LOW, fg=config.COLOR_BG,
                               pady=6, padx=12, anchor="w")
        self._label.pack(fill="x")

    def update(self, alerts: list[dict]):
        if not alerts:
            self.pack_forget()
            return

        # Show the highest-priority alert
        priority = {"urgent": 0, "low": 1, "high": 1, "warning": 2}
        top = min(alerts, key=lambda a: priority.get(a["level"], 9))

        color = {
            "urgent":  config.COLOR_LOW,
            "low":     config.COLOR_LOW,
            "high":    config.COLOR_HIGH,
            "warning": config.COLOR_WARNING,
        }.get(top["level"], config.COLOR_WARNING)

        self._label.config(text=f"  {top['message']}", bg=color,
                           fg=config.COLOR_BG)
        self.pack(fill="x", before=self.master.winfo_children()[0])


# ── Alert Settings Dialog ─────────────────────────────────────────────────────

class AlertSettingsDialog(tk.Toplevel):
    """
    Modal dialog for configuring alert thresholds.
    Calls on_save(settings_dict) when the user saves.
    """

    def __init__(self, parent, current_settings: dict, on_save):
        super().__init__(parent)
        self.title("Alert Settings")
        self.configure(bg=config.COLOR_BG)
        self.resizable(False, False)
        self.grab_set()   # modal

        self._on_save = on_save
        self._settings = dict(current_settings)
        self._build(current_settings)

        # Center over parent
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2 - 200
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - 200
        self.geometry(f"400x420+{px}+{py}")

    def _build(self, s: dict):
        pad = {"padx": 24, "pady": 6}

        tk.Label(self, text="Alert Settings", bg=config.COLOR_BG,
                 fg=config.COLOR_TEXT,
                 font=config.FONT_HEADING).pack(pady=(20, 4))
        tk.Label(self,
                 text="Desktop notifications fire when thresholds are crossed.",
                 bg=config.COLOR_BG, fg=config.COLOR_SUBTEXT,
                 font=config.FONT_SMALL).pack(pady=(0, 16))

        # Enable toggle
        self._enabled_var = tk.BooleanVar(value=s.get("alerts_enabled", True))
        tk.Checkbutton(self, text="Enable alerts",
                       variable=self._enabled_var,
                       bg=config.COLOR_BG, fg=config.COLOR_TEXT,
                       selectcolor=config.COLOR_PANEL,
                       activebackground=config.COLOR_BG,
                       font=config.FONT_BODY).pack(anchor="w", **pad)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24,
                                                       pady=8)

        form = tk.Frame(self, bg=config.COLOR_BG)
        form.pack(padx=24, fill="x")

        self._vars = {}
        fields = [
            ("alert_low",        "Low threshold (mg/dL)",       s.get("alert_low",       config.ALERT_LOW_DEFAULT)),
            ("alert_high",       "High threshold (mg/dL)",      s.get("alert_high",      config.ALERT_HIGH_DEFAULT)),
            ("rapid_rise_rate",  "Rapid rise rate (mg/dL/min)", s.get("rapid_rise_rate", config.ALERT_RAPID_RISE_RATE)),
            ("rapid_fall_rate",  "Rapid fall rate (mg/dL/min)", s.get("rapid_fall_rate", config.ALERT_RAPID_FALL_RATE)),
        ]

        for row, (key, label, default) in enumerate(fields):
            tk.Label(form, text=label, bg=config.COLOR_BG,
                     fg=config.COLOR_TEXT,
                     font=config.FONT_BODY).grid(row=row, column=0,
                                                  sticky="w", pady=5)
            var = tk.StringVar(value=str(default))
            self._vars[key] = var
            ttk.Entry(form, textvariable=var, width=10).grid(
                row=row, column=1, padx=(12, 0), pady=5, sticky="e")

        form.columnconfigure(0, weight=1)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=12)

        btn_row = tk.Frame(self, bg=config.COLOR_BG)
        btn_row.pack(pady=(0, 20))
        ttk.Button(btn_row, text="Cancel",
                   command=self.destroy).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Save",
                   command=self._save).pack(side="left", padx=6)

    def _save(self):
        try:
            new = {
                "alerts_enabled":  self._enabled_var.get(),
                "alert_low":       int(self._vars["alert_low"].get()),
                "alert_high":      int(self._vars["alert_high"].get()),
                "rapid_rise_rate": float(self._vars["rapid_rise_rate"].get()),
                "rapid_fall_rate": float(self._vars["rapid_fall_rate"].get()),
            }
            self._on_save(new)
            self.destroy()
        except ValueError:
            tk.Label(self, text="Please enter valid numbers.",
                     bg=config.COLOR_BG, fg=config.COLOR_LOW,
                     font=config.FONT_SMALL).pack()