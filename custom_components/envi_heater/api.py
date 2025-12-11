import aiohttp
import base64
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from aiohttp import ClientTimeout

_LOGGER = logging.getLogger(__name__)


class EnviApiError(Exception):
    """Base exception for Envi API errors."""
    pass


class EnviAuthenticationError(EnviApiError):
    """Raised when authentication fails."""
    pass


class EnviDeviceError(EnviApiError):
    """Raised when device operations fail."""
    pass


class EnviApiClient:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str):
        self.session = session
        self.username = username
        self.password = password
        self.base_url = "https://app-apis.enviliving.com/apis/v1"
        self.token: str | None = None
        self.token_expires: datetime | None = None
        self._refresh_lock = asyncio.Lock()
        self.timeout = ClientTimeout(total=15)

    async def authenticate(self) -> None:
        """Authenticate with fresh device_id. Debug output only when enabled."""
        fresh_device_id = f"ha_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

        payload = {
            "username": self.username,
            "password": self.password,
            "login_type": 1,
            "device_id": fresh_device_id,
            "device_type": "homeassistant",
        }

        url = f"{self.base_url}/auth/login"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-Envi/1.0",
        }

        # Debug-only – silent unless user enables debug logging
        _LOGGER.debug("Envi login attempt – device_id: %s", fresh_device_id)
        _LOGGER.debug("Login payload: %s", payload)

        try:
            async with self.session.post(url, json=payload, headers=headers, timeout=self.timeout) as resp:
                resp_text = await resp.text()

                _LOGGER.debug("Envi login response: %s – %.1000s", resp.status, resp_text)

                if resp.status != 200:
                    raise EnviAuthenticationError(f"Login failed: HTTP {resp.status}")

                data = json.loads(resp_text)
                if data.get("status") != "success":
                    msg = data.get("msg", "unknown error")
                    raise EnviAuthenticationError(f"Envi rejected login: {msg}")

                self.token = data["data"]["token"]
                jwt_exp = self._parse_jwt_expiry(self.token)
                self.token_expires = jwt_exp or (datetime.now(timezone.utc) +
