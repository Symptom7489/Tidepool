# 🩺 Tidepool Monitor

A desktop application for monitoring glucose and insulin data from the
[Tidepool](https://tidepool.org) platform, built for use with the
**twiist AID insulin system**.

Displays real-time CGM glucose readings, trend arrows, time-in-range stats,
bolus history, and alerts — with a full dashboard view and a minimal
always-on-top overlay mode.

> ⚠️ **Note:** This app reads data from Tidepool's servers, not directly from
> the pump. Expect a 5–15 minute lag from the twiist app sync.

---

## Screenshots

| Full Dashboard  | Mini Overlay    |
| --------------- | --------------- |
| _(coming soon)_ | _(coming soon)_ |

---

## Requirements

- Python 3.10 or higher (tested on 3.14)
- A [Tidepool account](https://app.tidepool.org/signup) with data synced from the twiist app
- Windows, macOS, or Linux

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/tidepool-monitor.git
cd tidepool-monitor
```

**2. Install dependencies**

```bash
pip install requests matplotlib
```

> Optional — for desktop notifications on Windows:
>
> ```bash
> pip install win10toast
> ```

**3. Configure your credentials**

Copy the example env file and fill in your details:

```bash
cp .env.example .env
```

Then edit `.env`:

```
TIDEPOOL_EMAIL=you@example.com
TIDEPOOL_PASSWORD=yourpassword
```

See [Configuration](#configuration) below for all available options.

**4. Run the app**

```bash
python main.py
```

---

## Project Structure

```
tidepool-monitor/
├── main.py              # Entry point
├── config.py            # All constants, colors, and .env loading
├── api.py               # Tidepool API client
├── data.py              # Data parsing, TIR, trend calculations
├── .env                 # Your credentials (never committed)
├── .env.example         # Template for .env
└── ui/
    ├── app.py           # Root window, manages frame switching
    ├── login.py         # Login screen
    ├── dashboard.py     # Main dashboard (stats, chart, controls)
    ├── mini.py          # Minimal always-on-top glucose overlay
    └── alerts.py        # Alert settings, notifications, banner
```

---

## Configuration

All settings live in your `.env` file. None are required except credentials.

| Variable                   | Default     | Description                            |
| -------------------------- | ----------- | -------------------------------------- |
| `TIDEPOOL_EMAIL`           | —           | Your Tidepool account email            |
| `TIDEPOOL_PASSWORD`        | —           | Your Tidepool account password         |
| `TIDEPOOL_PATIENT_ID`      | auto-detect | Override which patient's data to load  |
| `GLUCOSE_LOW`              | `70`        | Low glucose threshold (mg/dL)          |
| `GLUCOSE_HIGH`             | `180`       | High glucose threshold (mg/dL)         |
| `REFRESH_INTERVAL_SECONDS` | `300`       | Auto-refresh interval (0 to disable)   |
| `MINI_MODE_DEFAULT`        | `false`     | Launch in mini overlay mode by default |
| `MINI_WINDOW_SIZE`         | `260x110`   | Size of the mini overlay window        |

---

## Features

**Full Dashboard**

- Glucose chart with color-coded readings (green/red/orange by range)
- Time in Range, Time Low, Time High, Average BG, and Bolus count tiles
- Adjustable time range: 6 hours → 30 days
- Bolus dose markers on the chart
- Auto-refresh on a configurable interval

**Mini Overlay**

- Always-on-top compact window showing current glucose + trend arrow
- Color-coded background based on glucose status
- Draggable — reposition anywhere on screen
- Double-click to return to full dashboard

**Alerts**

- Desktop notifications for low, high, urgent, and rapid rise/fall
- Configurable thresholds via the Alerts panel in the dashboard
- Inline banner in the dashboard for active alerts
- Works on macOS, Linux, and Windows (with win10toast)

---

## How Tidepool Sync Works

This app reads from Tidepool's API, which is populated by the **twiist app**
running on your (or your child's) phone. The twiist app periodically syncs
CGM and pump data to Tidepool's servers.

If you are a **parent or caregiver**, you can either:

- Log in with your child's Tidepool credentials directly, or
- Have your child share their data with your Tidepool account, then log in
  with your own credentials — the app will detect the shared patient
  automatically.

---

## Sharing Data (Parent / Caregiver Setup)

1. Your child logs into [app.tidepool.org](https://app.tidepool.org)
2. Goes to **Profile → Share** and invites your email
3. You accept the invite in your own Tidepool account
4. Log into this app with **your** credentials — it will automatically
   load their data

---

## Notifications

| Platform | Method        | Setup required           |
| -------- | ------------- | ------------------------ |
| macOS    | `osascript`   | None — built in          |
| Linux    | `notify-send` | Usually pre-installed    |
| Windows  | `win10toast`  | `pip install win10toast` |

---

## Disclaimer

This is an **unofficial, community-built tool** and is not affiliated with
Tidepool, Sequel Medical Tech (twiist), or Abbott (FreeStyle Libre).
It is intended for informational use only and should not be used as a
substitute for your medical device's own alerts and monitoring.

Always follow your healthcare provider's guidance for managing diabetes.

---

## Contributing

Pull requests welcome. If you're adding a feature, please open an issue first
to discuss. Keep new modules consistent with the existing structure —
API calls in `api.py`, data transforms in `data.py`, new UI panels as
separate files in `ui/`.

---

## License

MIT

```

Also create a `.env.example` file to go alongside it — this is the safe template people can copy:
```

# Tidepool Monitor — configuration template

# Copy this file to .env and fill in your details

# Never commit .env to version control

TIDEPOST_EMAIL=you@example.com
TIDEPOOL_PASSWORD=yourpassword

# Optional: override which patient's data to show

# TIDEPOOL_PATIENT_ID=

# Glucose thresholds in mg/dL

# GLUCOSE_LOW=70

# GLUCOSE_HIGH=180

# Auto-refresh interval in seconds (0 to disable)

# REFRESH_INTERVAL_SECONDS=300

# Launch in mini overlay mode by default

# MINI_MODE_DEFAULT=false

# Mini overlay window size

# MINI_WINDOW_SIZE=260x110
