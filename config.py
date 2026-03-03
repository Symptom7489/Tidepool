"""
All constants, colors, thresholds, and .env loading.
Never scatter magic values in other files — put them here.

Optional .env file in the same directory:
    TIDEPOOL_EMAIL=you@example.com
    TIDEPOOL_PASSWORD=yourpassword
    TIDEPOOL_PATIENT_ID=optional_user_id_override
    GLUCOSE_LOW=70
    GLUCOSE_HIGH=180
    REFRESH_INTERVAL_SECONDS=300
"""

import os
from pathlib import Path

# ── Load .env manually (no extra dependencies) ───────────────────────────────
_ENV_PATH = Path(__file__).parent / ".env"

def _load_env_file():
    if not _ENV_PATH.exists():
        return
    with open(_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key   = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

_load_env_file()

# ── API ───────────────────────────────────────────────────────────────────────
BASE_URL       = "https://api.tidepool.org"
ENV_EMAIL      = os.environ.get("TIDEPOOL_EMAIL",     "")
ENV_PASSWORD   = os.environ.get("TIDEPOOL_PASSWORD",  "")
ENV_PATIENT_ID = os.environ.get("TIDEPOOL_PATIENT_ID","")  # optional override

# ── Glucose thresholds (mg/dL) ────────────────────────────────────────────────
GLUCOSE_LOW       = int(os.environ.get("GLUCOSE_LOW",  70))
GLUCOSE_HIGH      = int(os.environ.get("GLUCOSE_HIGH", 180))
GLUCOSE_VERY_LOW  = 54   # urgent low — fixed per clinical standard
GLUCOSE_VERY_HIGH = 250  # urgent high

# ── Auto-refresh ──────────────────────────────────────────────────────────────
REFRESH_INTERVAL_SECONDS = int(os.environ.get("REFRESH_INTERVAL_SECONDS", 300))

# ── Time range options ────────────────────────────────────────────────────────
TIME_RANGE_OPTIONS = ["6 hours","12 hours","24 hours","3 days","7 days","14 days","30 days"]
DEFAULT_TIME_RANGE = "24 hours"
TIME_RANGE_HOURS   = {
    "6 hours": 6, "12 hours": 12, "24 hours": 24,
    "3 days": 72, "7 days": 168,  "14 days": 336, "30 days": 720,
}

# ── Alert defaults ────────────────────────────────────────────────────────────
ALERT_LOW_DEFAULT     = GLUCOSE_LOW
ALERT_HIGH_DEFAULT    = GLUCOSE_HIGH
ALERT_RAPID_RISE_RATE =  3   # mg/dL per minute
ALERT_RAPID_FALL_RATE = -3   # mg/dL per minute

# ── Colors ────────────────────────────────────────────────────────────────────
COLOR_BG       = "#1e1e2e"
COLOR_PANEL    = "#2a2a3e"
COLOR_ACCENT   = "#7c6af7"
COLOR_LOW      = "#f38ba8"
COLOR_HIGH     = "#fab387"
COLOR_IN_RANGE = "#a6e3a1"
COLOR_TEXT     = "#cdd6f4"
COLOR_SUBTEXT  = "#6c7086"
COLOR_LINE     = "#89b4fa"
COLOR_WARNING  = "#f9e2af"

# ── Typography ────────────────────────────────────────────────────────────────
FONT_FAMILY  = "Helvetica"
FONT_TITLE   = (FONT_FAMILY, 22, "bold")
FONT_HEADING = (FONT_FAMILY, 15, "bold")
FONT_BODY    = (FONT_FAMILY, 11)
FONT_SMALL   = (FONT_FAMILY, 9)
FONT_STAT    = (FONT_FAMILY, 16, "bold")

# ── Window ────────────────────────────────────────────────────────────────────
WINDOW_TITLE = "Tidepool Diabetes Dashboard"
WINDOW_SIZE  = "1140x780"

# ── Mini mode ─────────────────────────────────────────────────────────────────
# Set to true to launch in compact overlay mode by default
MINI_MODE_DEFAULT = os.environ.get("MINI_MODE_DEFAULT", "false").lower() == "true"
MINI_WINDOW_SIZE  = "180x110"   # compact overlay dimensions