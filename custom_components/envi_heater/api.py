import aiohttp
import asyncio
import base64
import json
import logging
from aiohttp import ClientTimeout
from datetime import datetime, timedelta, timezone

_LOGGER = logging.getLogger(__name__)


class EnviApiError(Exception):
    """Base exception for Envi API errors."""
    pass


class EnviAuthenticationError(EnviApiError):
    """Authentication failed."""
    pass


class EnviDeviceError(EnviApiError):
    """Device operation failed."""
    pass


class EnviApiClient:
    """Central API client with token management for all devices."""

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
        """Authenticate and get access token."""
        payload = {
            "username": self.username,
            "password": self.password,
            "login_type": 1,
            "device_id": "homeassistant_integration",
            "device_type": "homeassistant",
        }

        try:
            response_data = await self._request("post", "auth/login", json=payload)
            self.token = response_data["data"]["token"]

            expires_in = response_data["data"].get("expires_in")
            self.token_expires = datetime.now(timezone.utc) + timedelta(
                seconds=expires_in or 3600
            )

            # Use real JWT expiry (this is what makes it rock-solid like the Hubitat version)
            jwt_expiry = self._parse_jwt_expiry(self.token)
            if jwt_expiry and jwt_expiry > self.token_expires:
                _LOGGER.info(
                    "Corrected token expiry using JWT → now valid for ~1 year"
                )
                self.token_expires = jwt_expiry

            _LOGGER.debug("Authentication successful")
        except Exception as err:
            raise EnviAuthenticationError(f"Authentication failed: {err}") from err

    def _parse_jwt_expiry(self, token: str) -> datetime | None:
        """Parse the real 'exp' claim from the JWT token."""
        try:
            payload_b64 = token.split(".")[1]
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64)
            claims = json.loads(payload_json)
            exp = claims.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, tz=timezone.utc)
        except Exception as exc:
            _LOGGER.debug("JWT expiry parse failed (%s) — using expires_in", exc)
        return None

    async def _is_token_valid(self) -> bool:
        """Check if current token is still valid (5-minute buffer)."""
        if not self.token or not self.token_expires:
            return False
        return datetime.now(timezone.utc) < (self.token_expires - timedelta(minutes=5))

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Perform API request with automatic token refresh on 401/403."""
        if not self.token:
            await self.authenticate()

        headers = kwargs.setdefault("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        headers.setdefault("Accept", "application/json")

        url = f"{self.base_url}/{endpoint}"

        async with self._refresh_lock:
            try:
                async with self.session.request(
                    method.upper(), url, timeout=self.timeout, **kwargs
                ) as response:
                    if response.status in (401, 403):
                        _LOGGER.debug("Token invalid (%s) — refreshing", response.status)
                        await self.authenticate()
                        headers["Authorization"] = f"Bearer {self.token}"
                        async with self.session.request(
                            method.upper(), url, timeout=self.timeout, headers=headers, **kwargs
                        ) as retry:
                            retry.raise_for_status()
                            return await retry.json()

                    response.raise_for_status()
                    return await response.json()

            except Exception as err:
                _LOGGER.error(f"API request failed ({method} {endpoint}): {err}")
                raise EnviDeviceError(f"API request failed: {err}") from err

    # ────────────────────── Device methods ──────────────────────

    async def fetch_all_device_ids(self):
        data = await self._request("GET", "device/list")
        return [device["id"] for device in data.get("data", [])]

    async def get_device_state(self, device_id: str) -> dict:
        data = await self._request("GET", f"device/{device_id}")
        return data.get("data", {})

    async def update_device(self, device_id: str, payload: dict):
        return await self._request("PATCH", f"device/update-temperature/{device_id}", json=payload)

    async def get_device_info(self, device_id: str) -> dict:
        data = await self._request("GET", f"device/info/{device_id}")
        return data.get("data", {})

    async def test_connection(self) -> bool:
        try:
            await self.fetch_all_device_ids()
            return True
        except Exception:
            return False
