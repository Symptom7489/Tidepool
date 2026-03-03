"""
ui/login.py — Login frame.
Tries .env credentials automatically on show; falls back to manual entry.
"""

import tkinter as tk
from tkinter import ttk
import threading

import requests

import config


class LoginFrame(tk.Frame):
    def __init__(self, parent, on_success):
        """
        on_success(user_id, display_name) — called after successful login.
        """
        super().__init__(parent, bg=config.COLOR_BG)
        self._on_success = on_success
        self._build()

    def _build(self):
        tk.Label(self, text="🩺  Tidepool Dashboard",
                 bg=config.COLOR_BG, fg=config.COLOR_TEXT,
                 font=config.FONT_TITLE).pack(pady=(70, 6))

        tk.Label(self,
                 text="Sign in with your Tidepool account\n"
                      "(yours if he's shared data with you, or his directly)",
                 bg=config.COLOR_BG, fg=config.COLOR_SUBTEXT,
                 font=config.FONT_BODY).pack(pady=(0, 28))

        form = tk.Frame(self, bg=config.COLOR_BG)
        form.pack()

        self.email_var = tk.StringVar(value=config.ENV_EMAIL)
        self.pass_var  = tk.StringVar(value=config.ENV_PASSWORD)

        for row, (label, var, show) in enumerate([
            ("Email",    self.email_var, ""),
            ("Password", self.pass_var,  "•"),
        ]):
            tk.Label(form, text=label, bg=config.COLOR_BG,
                     fg=config.COLOR_TEXT,
                     font=config.FONT_BODY).grid(row=row, column=0,
                                                  sticky="w", pady=5)
            ttk.Entry(form, textvariable=var, show=show, width=34).grid(
                row=row, column=1, padx=(12, 0), pady=5)

        self.status_lbl = tk.Label(self, text="", bg=config.COLOR_BG,
                                   fg=config.COLOR_LOW,
                                   font=config.FONT_SMALL)
        self.status_lbl.pack(pady=(14, 4))

        ttk.Button(self, text="Sign In",
                   command=self._attempt_login).pack()

        tk.Label(self,
                 text="⚠  Data reflects Tidepool sync, not live pump data.\n"
                      "Typical lag from twiist: 5–15 minutes.",
                 bg=config.COLOR_BG, fg=config.COLOR_SUBTEXT,
                 font=config.FONT_SMALL).pack(pady=(22, 0))

    def show(self, client):
        """Call this when the frame is displayed. Auto-login if .env is set."""
        self._client = client
        if config.ENV_EMAIL and config.ENV_PASSWORD:
            self.status_lbl.config(
                text="Signing in from .env…", fg=config.COLOR_SUBTEXT)
            self.after(100, self._attempt_login)

    def _attempt_login(self):
        email = self.email_var.get().strip()
        pw    = self.pass_var.get()
        if not email or not pw:
            self.status_lbl.config(text="Please enter email and password.",
                                   fg=config.COLOR_LOW)
            return
        self.status_lbl.config(text="Signing in…", fg=config.COLOR_SUBTEXT)
        self.update()
        threading.Thread(target=self._login_worker,
                         args=(email, pw), daemon=True).start()

    def _login_worker(self, email, pw):
        try:
            user = self._client.login(email, pw)
            uid  = user.get("userid")

            # Prefer a shared patient over the logged-in account
            patient_id   = config.ENV_PATIENT_ID or uid
            patient_name = user.get("username", email)

            if not config.ENV_PATIENT_ID:
                try:
                    shared = self._client.get_shared_users()
                    others = {k: v for k, v in shared.items() if k != uid}
                    if others:
                        patient_id   = list(others.keys())[0]
                        patient_name = f"shared patient ({patient_id[:8]}…)"
                except Exception:
                    pass

            self.after(0, lambda: self._on_success(patient_id, patient_name))

        except requests.HTTPError as e:
            code = e.response.status_code
            msg  = "Invalid email or password." if code in (401, 403) \
                   else f"Login failed (HTTP {code})."
            self.after(0, lambda: self.status_lbl.config(
                text=msg, fg=config.COLOR_LOW))
        except Exception as e:
            self.after(0, lambda: self.status_lbl.config(
                text=f"Connection error: {e}", fg=config.COLOR_LOW))