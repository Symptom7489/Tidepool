"""
api.py — Tidepool API client.
All network calls live here. Nothing else should import `requests`.
"""

import requests
from datetime import datetime


class TidepoolClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session  = requests.Session()
        self.token    = None
        self.user_id  = None

    def login(self, email: str, password: str) -> dict:
        resp = self.session.post(
            f"{self.base_url}/auth/login",
            auth=(email, password),
            timeout=15,
        )
        resp.raise_for_status()
        self.token = resp.headers.get("x-tidepool-session-token")
        self.session.headers.update({"x-tidepool-session-token": self.token})
        body = resp.json()
        self.user_id = body.get("userid")
        return body

    def logout(self):
        if self.token:
            try:
                self.session.post(f"{self.base_url}/auth/logout", timeout=5)
            except Exception:
                pass
        self.token   = None
        self.user_id = None

    def get_shared_users(self) -> dict:
        """Users who have shared their data with the logged-in account."""
        resp = self.session.get(
            f"{self.base_url}/access/groups/{self.user_id}",
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_data(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
        data_types: str = "cbg,smbg,bolus,basal,wizard",
    ) -> list:
        """
        Fetch diabetes device data for a user.
          cbg    – CGM glucose readings (stored in mmol/L)
          smbg   – finger-stick glucose
          bolus  – bolus insulin doses
          basal  – basal rate records
          wizard – bolus calculator entries (carbs, correction)
        """
        resp = self.session.get(
            f"{self.base_url}/data/{user_id}",
            params={
                "type":      data_types,
                "startDate": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endDate":   end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    @property
    def is_logged_in(self) -> bool:
        return self.token is not None