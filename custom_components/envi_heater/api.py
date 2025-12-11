import aiohttp
import asyncio
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
        """Authenticate with Envi cloud – fresh device_id on every login."""
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

        # Debug-only logging – only visible when user enables debug mode
        _LOGGER.debug("Envi login attempt – device_id: %s", fresh_device_id)
        _LOGGER.debug("Login payload: %s", payload)

        try:
            async with self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            ) as resp:
                resp_text = await resp.text()

                _LOGGER.debug("Envi login response: %s – %s", resp.status, resp_text[:1000])

                if resp.status != 200:
                    raise EnviAuthenticationError(f"Login failed with status {resp.status}")

                data = json.loads(resp_text)
                if data.get("status") != "success":
                    raise EnviAuthenticationError(
                        f"Envi rejected login: {data.get('msg', 'unknown')}"
                    )

                self.token = data["data"]["token"]
                jwt_exp = self._parse_jwt_expiry(self.token)
                # Fallback: assume 1 year validity if parsing fails
                self.token_expires = jwt_exp or (
                    datetime.now(timezone.utc) + timedelta(days=365)
                )

                _LOGGER.info(
                    "Envi login successful – token valid until %s",
                    self.token_expires.strftime("%Y-%m-%d %H:%M"),
                )

        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Envi authentication failed", exc_info=True)
            raise EnviAuthenticationError("Authentication failed") from err

    def _parse_jwt_expiry(self, token: str) -> datetime | None:
        """Extract real expiry from JWT (valid ~1 year)."""
        try:
            payload_part = token.split(".")[1]
            # Add padding
            payload_part += "=" * (-len(payload_part) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload_part))

            exp = claims.get("exp")
            if exp is not None:
                return datetime.fromtimestamp(int(exp), tz=timezone.utc)
        except Exception as e:  # noqa: BLE001
            _LOGGER.debug("Failed to parse JWT expiry: %s", e)

        return None

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Internal request handler with automatic token refresh."""
        if not self.token:
            await self.authenticate()

        # Refresh if within 5 minutes of expiry
        if self.token_expires and datetime.now(timezone.utc) >= self.token_expires - timedelta(minutes=5):
            async with self._refresh_lock:
                if self.token_expires and datetime.now(timezone.utc) >= self.token_expires - timedelta(minutes=5):
                    await self.authenticate()

        headers = kwargs.pop("headers", {}) or {}
        headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
            }
        )
        kwargs["headers"] = headers

        url = f"{self.base_url}/{endpoint}"

        async with self.session.request(
            method.upper(),
            url,
            timeout=self.timeout,
            **kwargs,
        ) as resp:
            if resp.status in (401, 403):
                _LOGGER.debug("Token expired/invalid – refreshing and retrying")
                async with self._refresh_lock:
                    await self.authenticate()
                    headers["Authorization"] = f"Bearer {self.token}"
                    kwargs["headers"] = headers

                async with self.session.request(
                    method.upper(),
                    url,
                    timeout=self.timeout,
                    **kwargs,
                ) as retry:
                    retry.raise_for_status()
                    return await retry.json()

            resp.raise_for_status()
            return await resp.json()

    # Public helpers
    async def fetch_all_device_ids(self) -> list[str]:
        data = await self._request("GET", "device/list")
        return [d["id"] for d in data.get("data", [])]

    async def get_device_state(self, device_id: str) -> dict:
        data = await self._request("GET", f"device/{device_id}")
        return data.get("data", {})

    async def update_device(self, device_id: str, payload: dict):
        return await self._request(
            "PATCH",
            f"device/update-temperature/{device_id}",
            json=payload,
        )

    async def test_connection(self) -> bool:
        try:
            await self.fetch_all_device_ids()
            return True
        except Exception:  # noqa: BLE001
            return False
