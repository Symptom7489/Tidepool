"""
ui/dashboard.py — Main dashboard frame: stats tiles, chart, top bar.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone, timedelta
import threading

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

import config
import data as datalib
from ui.alerts import AlertManager, AlertBanner, AlertSettingsDialog


class DashboardFrame(tk.Frame):
    def __init__(self, parent, client, on_logout):
        super().__init__(parent, bg=config.COLOR_BG)
        self._client       = client
        self._on_logout    = on_logout
        self._patient_id   = None
        self._buckets      = {}
        self._alert_mgr    = AlertManager()
        self._refresh_job  = None
        self._mini_overlay = None

        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self._build_topbar()
        self._alert_banner = AlertBanner(self)
        self._build_controls()
        self._build_stats()
        self._build_chart()
        self._build_statusbar()

    def _build_topbar(self):
        top = tk.Frame(self, bg=config.COLOR_PANEL, height=52)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="🩺  Tidepool Dashboard",
                 bg=config.COLOR_PANEL, fg=config.COLOR_TEXT,
                 font=config.FONT_HEADING).pack(side="left", padx=16)

        ttk.Button(top, text="Sign Out",
                   command=self._do_logout).pack(side="right", padx=8, pady=8)
        ttk.Button(top, text="⟳  Refresh",
                   command=self.refresh).pack(side="right", padx=4, pady=8)
        ttk.Button(top, text="🔔  Alerts",
                   command=self._open_alert_settings).pack(side="right",
                                                            padx=4, pady=8)
        ttk.Button(top, text="⊟  Mini",
                   command=self._toggle_mini).pack(side="right", padx=4, pady=8)

    def _build_controls(self):
        ctrl = tk.Frame(self, bg=config.COLOR_BG, pady=8)
        ctrl.pack(fill="x", padx=16)

        tk.Label(ctrl, text="Viewing:", bg=config.COLOR_BG,
                 fg=config.COLOR_SUBTEXT,
                 font=config.FONT_BODY).pack(side="left")

        self._user_lbl = tk.Label(ctrl, text="—", bg=config.COLOR_BG,
                                   fg=config.COLOR_ACCENT,
                                   font=(config.FONT_FAMILY, 11, "bold"))
        self._user_lbl.pack(side="left", padx=(4, 20))

        tk.Label(ctrl, text="Range:", bg=config.COLOR_BG,
                 fg=config.COLOR_SUBTEXT,
                 font=config.FONT_BODY).pack(side="left")

        self._range_var = tk.StringVar(value=config.DEFAULT_TIME_RANGE)
        cb = ttk.Combobox(ctrl, textvariable=self._range_var, width=12,
                          values=config.TIME_RANGE_OPTIONS, state="readonly")
        cb.pack(side="left", padx=(4, 0))
        cb.bind("<<ComboboxSelected>>", lambda _: self.refresh())

        self._updated_lbl = tk.Label(ctrl, text="", bg=config.COLOR_BG,
                                      fg=config.COLOR_SUBTEXT,
                                      font=config.FONT_SMALL)
        self._updated_lbl.pack(side="right")

        if config.REFRESH_INTERVAL_SECONDS > 0:
            mins = config.REFRESH_INTERVAL_SECONDS // 60
            tk.Label(ctrl, text=f"auto-refresh: {mins}m",
                     bg=config.COLOR_BG, fg=config.COLOR_SUBTEXT,
                     font=config.FONT_SMALL).pack(side="right", padx=(0, 10))

    def _build_stats(self):
        row = tk.Frame(self, bg=config.COLOR_BG)
        row.pack(fill="x", padx=16, pady=(0, 8))

        self._stats = {}
        defs = [
            ("latest",   "Latest BG",     config.COLOR_TEXT),
            ("tir",      "Time in Range", config.COLOR_IN_RANGE),
            ("tir_low",  "Time Low",      config.COLOR_LOW),
            ("tir_high", "Time High",     config.COLOR_HIGH),
            ("average",  "Average BG",    config.COLOR_TEXT),
            ("boluses",  "Boluses",       config.COLOR_TEXT),
        ]
        for key, lbl, color in defs:
            box = tk.Frame(row, bg=config.COLOR_PANEL, padx=14, pady=8)
            box.pack(side="left", expand=True, fill="both", padx=4)
            tk.Label(box, text=lbl, bg=config.COLOR_PANEL,
                     fg=config.COLOR_SUBTEXT,
                     font=config.FONT_SMALL).pack()
            v = tk.Label(box, text="—", bg=config.COLOR_PANEL,
                         fg=color, font=config.FONT_STAT)
            v.pack()
            self._stats[key] = v

    def _build_chart(self):
        chart_f = tk.Frame(self, bg=config.COLOR_BG)
        chart_f.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        self._fig = Figure(figsize=(11, 4), dpi=96, facecolor=config.COLOR_BG)
        self._ax  = self._fig.add_subplot(111)
        self._style_ax(self._ax)
        self._ax.set_title("Glucose — waiting for data…",
                           color=config.COLOR_TEXT, pad=10)

        self._canvas = FigureCanvasTkAgg(self._fig, master=chart_f)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    def _build_statusbar(self):
        self._status = tk.Label(self, text="Ready", bg=config.COLOR_PANEL,
                                fg=config.COLOR_SUBTEXT,
                                font=config.FONT_SMALL, anchor="w")
        self._status.pack(fill="x", side="bottom", ipady=4, padx=8)

    # ── Public API ────────────────────────────────────────────────────────────

    def show(self, patient_id: str, display_name: str):
        self._patient_id = patient_id
        self._user_lbl.config(text=display_name)
        self.refresh()
        self._schedule_auto_refresh()

    def refresh(self):
        if not self._client.is_logged_in or not self._patient_id:
            return
        self._set_status("Fetching data from Tidepool…")
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    # ── Mini overlay ──────────────────────────────────────────────────────────

    def _toggle_mini(self):
        from ui.mini import MiniOverlay
        self.winfo_toplevel().withdraw()
        self._mini_overlay = MiniOverlay(self.winfo_toplevel(), self._expand_from_mini)
        self._push_to_mini()

    def _expand_from_mini(self):
        if self._mini_overlay:
            self._mini_overlay.destroy()
            self._mini_overlay = None
        self.winfo_toplevel().deiconify()

    def _push_to_mini(self):
        if not self._mini_overlay:
            return
        glucose_events = (self._buckets.get("cbg", []) +
                          self._buckets.get("smbg", []))
        glucose_events.sort(key=lambda e: e.get("time", ""))
        _, values = datalib.glucose_series(glucose_events)
        latest = values[-1] if values else None
        trend  = datalib.glucose_trend(values)
        self._mini_overlay.update_glucose(latest, trend)

    # ── Data fetch ────────────────────────────────────────────────────────────

    def _fetch_worker(self):
        try:
            hours = config.TIME_RANGE_HOURS.get(self._range_var.get(), 24)
            end   = datetime.now(timezone.utc)
            start = end - timedelta(hours=hours)
            raw   = self._client.get_data(self._patient_id, start, end)
            self._buckets = datalib.parse_events(raw)
            self.after(0, self._update_ui)
        except Exception as e:
            self.after(0, lambda msg=str(e): self._set_status(f"Fetch error: {msg}"))

    def _update_ui(self):
        self._update_stats()
        self._update_chart()
        self._update_alerts()
        self._push_to_mini()
        now = datetime.now().strftime("%H:%M:%S")
        self._updated_lbl.config(text=f"Updated {now}")
        total = sum(len(v) for v in self._buckets.values())
        self._set_status(f"Loaded {total} events.")

    def _update_stats(self):
        glucose_events = (self._buckets.get("cbg", []) +
                          self._buckets.get("smbg", []))
        glucose_events.sort(key=lambda e: e.get("time", ""))
        _, values = datalib.glucose_series(glucose_events)

        if values:
            latest = values[-1]
            lc = (config.COLOR_LOW  if latest < config.GLUCOSE_LOW  else
                  config.COLOR_HIGH if latest > config.GLUCOSE_HIGH else
                  config.COLOR_IN_RANGE)
            self._stats["latest"].config(text=f"{latest} mg/dL", fg=lc)
            self._stats["average"].config(
                text=f"{round(sum(values)/len(values))} mg/dL",
                fg=config.COLOR_TEXT)
            tir = datalib.compute_tir(values, config.GLUCOSE_LOW,
                                      config.GLUCOSE_HIGH)
            self._stats["tir"].config(text=f"{tir['in_range']}%")
            self._stats["tir_low"].config(text=f"{tir['low']}%")
            self._stats["tir_high"].config(text=f"{tir['high']}%")
        else:
            for k in ("latest", "average", "tir", "tir_low", "tir_high"):
                self._stats[k].config(text="—", fg=config.COLOR_TEXT)

        self._stats["boluses"].config(
            text=str(len(self._buckets.get("bolus", []))))

    def _update_chart(self):
        self._ax.clear()
        self._style_ax(self._ax)

        glucose_events = (self._buckets.get("cbg", []) +
                          self._buckets.get("smbg", []))
        glucose_events.sort(key=lambda e: e.get("time", ""))
        times, values = datalib.glucose_series(glucose_events)

        if not times:
            self._ax.set_title("No glucose data in selected range",
                               color=config.COLOR_TEXT)
            self._canvas.draw()
            return

        self._ax.axhspan(0,                   config.GLUCOSE_LOW,
                         alpha=0.07, color=config.COLOR_LOW)
        self._ax.axhspan(config.GLUCOSE_HIGH,  400,
                         alpha=0.07, color=config.COLOR_HIGH)
        self._ax.axhline(config.GLUCOSE_LOW,   color=config.COLOR_LOW,
                         lw=0.8, linestyle="--", alpha=0.5)
        self._ax.axhline(config.GLUCOSE_HIGH,  color=config.COLOR_HIGH,
                         lw=0.8, linestyle="--", alpha=0.5)

        self._ax.plot(times, values, color=config.COLOR_LINE,
                      lw=1.5, alpha=0.7, zorder=2)
        for t, v in zip(times, values):
            c = (config.COLOR_LOW  if v < config.GLUCOSE_LOW  else
                 config.COLOR_HIGH if v > config.GLUCOSE_HIGH else
                 config.COLOR_IN_RANGE)
            self._ax.scatter(t, v, color=c, s=14, zorder=3, linewidths=0)

        for b in self._buckets.get("bolus", []):
            try:
                self._ax.axvline(datalib.parse_time(b["time"]),
                                 color=config.COLOR_ACCENT,
                                 lw=1, linestyle=":", alpha=0.5)
            except Exception:
                pass

        hours = config.TIME_RANGE_HOURS.get(self._range_var.get(), 24)
        if hours <= 24:
            self._ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            self._ax.xaxis.set_major_locator(
                mdates.HourLocator(interval=max(1, hours // 8)))
        else:
            self._ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
            self._ax.xaxis.set_major_locator(mdates.DayLocator())

        self._fig.autofmt_xdate(rotation=28, ha="right")
        self._ax.set_ylabel("mg/dL", color=config.COLOR_SUBTEXT, fontsize=9)
        self._ax.set_ylim(30, 360)
        self._ax.set_title(
            f"Glucose — last {self._range_var.get()}  "
            f"({len(values)} readings)  ·  purple dashes = bolus",
            color=config.COLOR_TEXT, pad=10, fontsize=10)
        self._fig.tight_layout()
        self._canvas.draw()

    def _update_alerts(self):
        glucose_events = (self._buckets.get("cbg", []) +
                          self._buckets.get("smbg", []))
        glucose_events.sort(key=lambda e: e.get("time", ""))
        times, values = datalib.glucose_series(glucose_events)
        active = self._alert_mgr.evaluate(values, times)
        self._alert_banner.update(active)

    # ── Auto-refresh ──────────────────────────────────────────────────────────

    def _schedule_auto_refresh(self):
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
        if config.REFRESH_INTERVAL_SECONDS > 0:
            ms = config.REFRESH_INTERVAL_SECONDS * 1000
            self._refresh_job = self.after(ms, self._auto_refresh)

    def _auto_refresh(self):
        self.refresh()
        self._schedule_auto_refresh()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _style_ax(self, ax):
        ax.set_facecolor(config.COLOR_PANEL)
        ax.tick_params(colors=config.COLOR_SUBTEXT, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(config.COLOR_SUBTEXT)
            spine.set_alpha(0.3)
        ax.grid(True, color=config.COLOR_SUBTEXT, alpha=0.15, linewidth=0.5)

    def _set_status(self, msg: str):
        self._status.config(text=msg)

    def _do_logout(self):
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
        self._client.logout()
        self._on_logout()

    def _open_alert_settings(self):
        AlertSettingsDialog(
            self,
            current_settings=self._alert_mgr.settings,
            on_save=self._alert_mgr.update_settings,
        )