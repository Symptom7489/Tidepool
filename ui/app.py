"""
ui/app.py — Root application window. Manages frame switching only.
"""

import tkinter as tk
from tkinter import ttk

import config
from api import TidepoolClient
from ui.login import LoginFrame
from ui.dashboard import DashboardFrame


class TidepoolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(config.WINDOW_TITLE)
        self.geometry(config.WINDOW_SIZE)
        self.configure(bg=config.COLOR_BG)
        self.resizable(True, True)

        self._client = TidepoolClient(base_url=config.BASE_URL)
        self._apply_styles()

        self._login_frame = LoginFrame(self, on_success=self._on_login)
        self._dash_frame  = DashboardFrame(self, self._client,
                                           on_logout=self._on_logout)
        self._show_login()

    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=config.COLOR_BG, foreground=config.COLOR_TEXT,
                    fieldbackground=config.COLOR_PANEL, font=config.FONT_BODY)
        s.configure("TLabel",  background=config.COLOR_BG,
                    foreground=config.COLOR_TEXT)
        s.configure("TButton", background=config.COLOR_ACCENT,
                    foreground="white", relief="flat", padding=6)
        s.map("TButton", background=[("active", "#5e52d8")])
        s.configure("TEntry",    fieldbackground=config.COLOR_PANEL,
                    foreground=config.COLOR_TEXT, insertcolor=config.COLOR_TEXT)
        s.configure("TCombobox", fieldbackground=config.COLOR_PANEL,
                    foreground=config.COLOR_TEXT,
                    selectbackground=config.COLOR_ACCENT)
        s.configure("TCheckbutton", background=config.COLOR_BG,
                    foreground=config.COLOR_TEXT)

    def _show_login(self):
        self._dash_frame.pack_forget()
        self._login_frame.pack(fill="both", expand=True)
        self._login_frame.show(self._client)

    def _show_dashboard(self, patient_id: str, name: str):
        self._login_frame.pack_forget()
        self._dash_frame.pack(fill="both", expand=True)
        self._dash_frame.show(patient_id, name)
        if config.MINI_MODE_DEFAULT:
            self.after(200, self._dash_frame._toggle_mini)

    def _on_login(self, patient_id: str, name: str):
        self._show_dashboard(patient_id, name)

    def _on_logout(self):
        self._show_login()