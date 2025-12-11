import aiohttp
import asyncio
import base64
import json
import logging
from aiohttp import ClientTimeout
from datetime import datetime, timedelta, timezone

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
        """Login and store token + real JWT expiry."""
        payload = {
            "username": self.username,
            "password": self.password,
            "login_type": 1,
            "device_id": f"ha_{__{__import__('uuid').getnode():x}",
            "device_type": "homeassistant",
        }

        # Direct request — no recursion, no lock needed here
        async with self.session.post(
            f"{self.base_url}/auth/login",
            json=payload,
            timeout=self.timeout,
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise EnviAuthenticationError(f"Login failed ({resp.status}): {text}")

            data = await resp.json()

        self.token = data["data"]["token"]

        # Use JWT expiry (real one, ~1 year) instead of broken expires_in
        jwt_expiry = self._parse_jwt_expiry(self.token)
        if jwt_expiry:
            self.token_expires = jwt_expiry
            _LOGGER.info("Envi token authenticated — valid until %s", jwt_expiry.strftime("%Y-%m-%d"))
        else:
            # Fallback (should never happen)
            self.token_expires = datetime.now(timezone.utc) + timedelta(days=365)

    def _parse_jwt_expiry(self, token: str) -> datetime | None:
        try:
            payload = token.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload))
            if claims.get("exp"):
                return datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        except Exception as e:
            _LOGGER.debug("JWT parse failed: %s", e)
        return None

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make API call — automatically refreshes token only on 401/403."""
        # Make sure we have a valid token before entering the lock
        if not self.token or not self.token_expires or datetime.now(timezone.utc) >= self.token_expires - timedelta(minutes=5):
            async with self._refresh_lock:  # prevent parallel refreshes
                # Double-check after acquiring lock
                if not self.token or datetime.now(timezone.utc) >= self.token_expires - timedelta(minutes=5):
                    await self.authenticate()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        headers["Accept"] = "application/json"
        kwargs["headers"] = headers

        url = f"{self.base_url}/{endpoint}"

        async with self.session.request(method.upper(), url, timeout=self.timeout, **kwargs) as resp:
            if resp.status in (401, 403):
                # Token was invalidated — refresh once and retry
                async with self._refresh_lock:
                    await self.authenticate()
                    headers["Authorization"] = f"Bearer {self.token}"
                    kwargs["headers"] = headers

                async with self.session.request(method.upper(), url, timeout=self.timeout, **kwargs) as retry_resp:
                    retry_resp.raise_for_status()
                    return await retry_resp.json()

            resp.raise_for_status()
            return await resp.json()

    # ────────────────── Simple helpers ──────────────────

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
