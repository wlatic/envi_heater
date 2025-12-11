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
    pass


class EnviAuthenticationError(EnviApiError):
    pass


class EnviDeviceError(EnviApiError):
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
        """Login with maximum possible debug output."""
        # Fresh device_id every single time the integration is added
        fresh_device_id = f"ha_debug_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

        payload = {
            "username": self.username,
            "password": self.password,
            "login_type": 1,
            "device_id": fresh_device_id,
            "device_type": "homeassistant",
        }

        url = f"{self.base_url}/auth/login"

        # === THIS IS THE IMPORTANT PART – FULL DEBUG LOGGING ===
        _LOGGER.warning("=== ENVI AUTH ATTEMPT ===")
        _LOGGER.warning("URL: %s", url)
        _LOGGER.warning("Payload → %s", payload)
        _LOGGER.warning("Username used: %s", self.username)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-Envi/1.0",
        }

        try:
            async with self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            ) as resp:

                resp_text = await resp.text()

                _LOGGER.warning("Envi server responded with HTTP %s", resp.status)
                _LOGGER.warning("Response headers: %s", dict(resp.headers))
                _LOGGER.warning("Response body (first 1500 chars): %s", resp_text[:1500])

                if resp.status == 200:
                    data = json.loads(resp_text)
                    self.token = data["data"]["token"]

                    # Parse real JWT expiry
                    jwt_exp = self._parse_jwt_expiry(self.token)
                    self.token_expires = jwt_exp or (datetime.now(timezone.utc) + timedelta(days=365))

                    _LOGGER.warning("ENVI LOGIN SUCCESSFUL – token valid until %s", self.token_expires.strftime("%Y-%m-%d %H:%M"))
                    return

                # Anything else = failure
                raise EnviAuthenticationError(f"Envi rejected login → HTTP {resp.status} – {resp_text[:500]}")

        except Exception as err:
            _LOGGER.error("Envi authentication crashed: %s", err, exc_info=True)
            raise EnviAuthenticationError(f"Login failed: {err}") from err

    def _parse_jwt_expiry(self, token: str) -> datetime | None:
        try:
            payload_part = token.split(".")[1]
            payload_part += "=" * (-len(payload_part) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload_part))
            if exp := claims.get("exp"):
                return datetime.fromtimestamp(exp, tz=timezone.utc)
        except Exception as e:
            _LOGGER.debug("JWT expiry parse failed: %s", e)
        return None

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        if not self.token:
            await self.authenticate()

        if datetime.now(timezone.utc) >= self.token_expires - timedelta(minutes=5):
            async with self._refresh_lock:
                if datetime.now(timezone.utc) >= self.token_expires - timedelta(minutes=5):
                    await self.authenticate()

        headers = kwargs.pop("headers", {})
        headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        })
        kwargs["headers"] = headers

        url = f"{self.base_url}/{endpoint}"

        async with self.session.request(method.upper(), url, timeout=self.timeout, **kwargs) as resp:
            if resp.status in (401, 403):
                async with self._refresh_lock:
                    await self.authenticate()
                    headers["Authorization"] = f"Bearer {self.token}"
                    kwargs["headers"] = headers
                async with self.session.request(method.upper(), url, timeout=self.timeout, **kwargs) as retry:
                    retry.raise_for_status()
                    return await retry.json()

            resp.raise_for_status()
            return await resp.json()

    # Simple helpers
    async def fetch_all_device_ids(self):
        data = await self._request("GET", "device/list")
        return [d["id"] for d in data.get("data", [])]

    async def get_device_state(self, device_id: str) -> dict:
        data = await self._request("GET", f"device/{device_id}")
        return data.get("data", {})

    async def update_device(self, device_id: str, payload: dict):
        return await self._request("PATCH", f"device/update-temperature/{device_id}", json=payload)

    async def test_connection(self) -> bool:
        try:
            await self.fetch_all_device_ids()
            return True
        except Exception:
            return False
