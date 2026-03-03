"""
ui/mini.py — Minimal glucose overlay.
"""

import tkinter as tk
import config
import sys


def _trend_arrow(rate):
    if rate is None:  return "→"
    if rate >=  3:    return "↑↑"
    if rate >=  2:    return "↑"
    if rate >=  1:    return "↗"
    if rate <= -3:    return "↓↓"
    if rate <= -2:    return "↓"
    if rate <= -1:    return "↘"
    return "→"


class MiniOverlay(tk.Toplevel):

    def __init__(self, parent, on_expand):
        self._on_expand = on_expand
        self._drag_x    = 0
        self._drag_y    = 0

        super().__init__()

        w, h = map(int, config.MINI_WINDOW_SIZE.split("x"))
        self.title("Tidepool Mini")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.geometry(f"{w}x{h}+{self.winfo_screenwidth() - w - 24}+{self.winfo_screenheight() - h - 60}")

        try:
            self.attributes("-alpha", 0.92)
        except Exception:
            pass

        self._build()
        self._bind_drag()
        self.update()
        self.overrideredirect(True)  

    def _on_close(self):
        sys.exit(0)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self._container = tk.Frame(self, bg=config.COLOR_PANEL, cursor="hand2")
        self._container.pack(fill="both", expand=True)

        self._glucose_lbl = tk.Label(
            self._container,
            text="---",
            bg=config.COLOR_PANEL,
            fg=config.COLOR_TEXT,
            font=(config.FONT_FAMILY, 30, "bold"),
        )
        self._glucose_lbl.pack(side="left", padx=(16, 4), pady=10)

        right = tk.Frame(self._container, bg=config.COLOR_PANEL)
        right.pack(side="left", fill="y", pady=10)

        self._arrow_lbl = tk.Label(
            right,
            text="→",
            bg=config.COLOR_PANEL,
            fg=config.COLOR_SUBTEXT,
            font=(config.FONT_FAMILY, 18),
        )
        self._arrow_lbl.pack(anchor="w")

        tk.Label(
            right,
            text="mg/dL",
            bg=config.COLOR_PANEL,
            fg=config.COLOR_SUBTEXT,
            font=(config.FONT_FAMILY, 8),
        ).pack(anchor="w")

        self._hint = tk.Label(
            self._container,
            text="⊞",
            bg=config.COLOR_PANEL,
            fg=config.COLOR_SUBTEXT,
            font=(config.FONT_FAMILY, 10),
            cursor="hand2",
        )
        self._hint.place(relx=1.0, rely=0.0, anchor="ne", x=-4, y=4)
        self._hint.bind("<Button-1>", lambda _: self._on_expand())

        for widget in (self._container, self._glucose_lbl, self._arrow_lbl):
            widget.bind("<Double-Button-1>", self._on_double_click)

    # ── Drag ──────────────────────────────────────────────────────────────────

    def _bind_drag(self):
        self._container.bind("<ButtonPress-1>",  self._drag_start)
        self._container.bind("<B1-Motion>",       self._drag_move)
        self._glucose_lbl.bind("<ButtonPress-1>", self._drag_start)
        self._glucose_lbl.bind("<B1-Motion>",      self._drag_move)

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")
    def _on_click(self, event):
        # Single click — only expand if it wasn't a drag
        if (abs(event.x_root - self.winfo_x() - self._drag_x) < 5 and
                abs(event.y_root - self.winfo_y() - self._drag_y) < 5):
            pass   # single click does nothing now

    def _on_double_click(self, event):
     self._on_expand()

    # ── Public update API ─────────────────────────────────────────────────────

    def update_glucose(self, value, trend_rate):
        if value is None:
            self._glucose_lbl.config(text="---", fg=config.COLOR_TEXT)
            self._arrow_lbl.config(text="?",     fg=config.COLOR_SUBTEXT)
            self._set_bg(config.COLOR_PANEL)
            return

        if value < config.GLUCOSE_VERY_LOW:
            fg, bg = config.COLOR_LOW,  "#3d1a22"
        elif value < config.GLUCOSE_LOW:
            fg, bg = config.COLOR_LOW,  "#2e1a20"
        elif value > 250:
            fg, bg = config.COLOR_HIGH, "#3d2a10"
        elif value > config.GLUCOSE_HIGH:
            fg, bg = config.COLOR_HIGH, "#2e2310"
        else:
            fg, bg = config.COLOR_IN_RANGE, config.COLOR_PANEL

        self._glucose_lbl.config(text=str(value), fg=fg)
        self._arrow_lbl.config(text=_trend_arrow(trend_rate), fg=fg)
        self._set_bg(bg)

    def _set_bg(self, color):
        self._container.config(bg=color)
        self._glucose_lbl.config(bg=color)
        self._arrow_lbl.config(bg=color)
        self._hint.config(bg=color)
        for child in self._container.winfo_children():
            try:
                child.config(bg=color)
                for grandchild in child.winfo_children():
                    grandchild.config(bg=color)
            except Exception:
                pass