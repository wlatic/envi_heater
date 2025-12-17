import asyncio
import base64
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

import aiohttp
from aiohttp import ClientTimeout

from .const import BASE_URL, ENDPOINTS

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
        self.base_url = BASE_URL
        self.token: str | None = None
        self.token_expires: datetime | None = None
        self._refresh_lock = asyncio.Lock()
        self.timeout = ClientTimeout(total=15)

    async def authenticate(self) -> None:
        """Log in to Envi with a fresh unique device_id."""
        fresh_device_id = f"ha_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        payload = {
            "username": self.username,
            "password": self.password,
            "login_type": 1,
            "device_id": fresh_device_id,
            "device_type": "homeassistant",
        }
        url = f"{self.base_url}/{ENDPOINTS['auth_login']}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-Envi/1.0",
        }
        _LOGGER.debug("Envi login attempt – device_id: %s", fresh_device_id)
        try:
            async with self.session.post(url, json=payload, headers=headers, timeout=self.timeout) as resp:
                resp_text = await resp.text()
                _LOGGER.debug("Envi login HTTP %s – %.1000s", resp.status, resp_text)
                if resp.status != 200:
                    raise EnviAuthenticationError(f"Login failed (HTTP {resp.status})")
                data = json.loads(resp_text)
                if data.get("status") != "success":
                    msg = data.get("msg", "unknown error")
                    raise EnviAuthenticationError(f"Envi rejected login: {msg}")
                self.token = data["data"]["token"]
                jwt_exp = self._parse_jwt_expiry(self.token)
                self.token_expires = jwt_exp or (datetime.now(timezone.utc) + timedelta(days=365))
                _LOGGER.info(
                    "Envi login successful – token valid until %s",
                    self.token_expires.strftime("%Y-%m-%d %H:%M"),
                )
        except Exception as err:
            _LOGGER.error("Envi authentication failed", exc_info=True)
            raise EnviAuthenticationError("Authentication failed") from err

    def _parse_jwt_expiry(self, token: str) -> datetime | None:
        """Extract real expiry from JWT token."""
        try:
            payload_part = token.split(".")[1]
            payload_part += "=" * (-len(payload_part) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload_part))
            exp = claims.get("exp")
            if exp:
                return datetime.fromtimestamp(int(exp), tz=timezone.utc)
        except Exception as e:
            _LOGGER.debug("Failed to parse JWT expiry: %s", e)
        return None

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Internal request with automatic token refresh and error handling."""
        if self.token is None:
            await self.authenticate()

        if (
            self.token_expires
            and datetime.now(timezone.utc) >= self.token_expires - timedelta(minutes=5)
        ):
            async with self._refresh_lock:
                if datetime.now(timezone.utc) >= self.token_expires - timedelta(minutes=5):
                    await self.authenticate()

        headers = kwargs.pop("headers", {}) or {}
        headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        })
        kwargs["headers"] = headers
        url = f"{self.base_url}/{endpoint}"

        try:
            async with self.session.request(method.upper(), url, timeout=self.timeout, **kwargs) as resp:
                if resp.status in (401, 403):
                    _LOGGER.info("Token expired – refreshing automatically")
                    async with self._refresh_lock:
                        await self.authenticate()
                        headers["Authorization"] = f"Bearer {self.token}"
                        kwargs["headers"] = headers
                    async with self.session.request(method.upper(), url, timeout=self.timeout, **kwargs) as retry:
                        retry.raise_for_status()
                        data = await retry.json()
                        if data.get("status") != "success" and retry.status not in (200, 201, 204):
                            msg = data.get("msg", "Unknown error")
                            raise EnviApiError(f"API error: {msg}")
                        return data
                
                # Don't raise on 400 - we want to handle it ourselves
                if resp.status == 400:
                    data = await resp.json()
                    msg = data.get("msg", "Bad Request")
                    msg_code = data.get("msgCode", "unknown")
                    _LOGGER.error("API returned 400 Bad Request: %s (code: %s). Payload may be invalid.", msg, msg_code)
                    raise EnviApiError(f"Bad Request: {msg} (code: {msg_code})")
                
                resp.raise_for_status()
                data = await resp.json()
                
                # Check API-level success status
                if data.get("status") != "success" and resp.status not in (200, 201, 204):
                    msg = data.get("msg", "Unknown error")
                    msg_code = data.get("msgCode", "unknown")
                    _LOGGER.warning("API returned error: %s (code: %s)", msg, msg_code)
                    raise EnviApiError(f"API error: {msg} (code: {msg_code})")
                
                return data
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error during API request: %s", err)
            raise EnviApiError(f"Network error: {err}") from err
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid JSON response from API")
            raise EnviApiError("Invalid response from API") from err

    async def fetch_all_device_ids(self) -> list[str]:
        data = await self._request("GET", ENDPOINTS["device_list"])
        return [d["id"] for d in data.get("data", [])]

    async def get_device_state(self, device_id: str) -> dict:
        endpoint = ENDPOINTS["device_get"].format(device_id=device_id)
        data = await self._request("GET", endpoint)
        return data.get("data", {})

    async def update_device(self, device_id: str, payload: dict) -> dict:
        """Update device temperature and/or state."""
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json=payload)

    async def set_temperature(self, device_id: str, temperature: float) -> dict:
        """Set target temperature for a device."""
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json={"temperature": temperature})

    async def set_state(self, device_id: str, state: int) -> dict:
        """Set device state (1 = on, 0 = off)."""
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json={"state": state})

    async def set_mode(self, device_id: str, mode: int) -> dict:
        """Set device mode (1 = heat, 3 = auto, etc.)."""
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json={"mode": mode})

    # Schedule Management
    async def get_schedule_list(self) -> list[dict]:
        """Get list of all schedules."""
        data = await self._request("GET", ENDPOINTS["schedule_list"])
        return data.get("data", [])

    async def get_schedule(self, schedule_id: int) -> dict:
        """Get a specific schedule by ID."""
        schedules = await self.get_schedule_list()
        for schedule in schedules:
            if schedule.get("id") == schedule_id:
                return schedule
        raise EnviDeviceError(f"Schedule {schedule_id} not found")

    async def create_schedule(self, schedule_data: dict) -> dict:
        """Create a new schedule."""
        return await self._request("POST", ENDPOINTS["schedule_add"], json=schedule_data)

    async def update_schedule(self, schedule_id: int, schedule_data: dict) -> dict:
        """Update an existing schedule."""
        endpoint = ENDPOINTS["schedule_update"].format(schedule_id=schedule_id)
        return await self._request("PUT", endpoint, json=schedule_data)

    async def delete_schedule(self, schedule_id: int) -> dict:
        """Delete a schedule."""
        endpoint = ENDPOINTS["schedule_delete"].format(schedule_id=schedule_id)
        return await self._request("DELETE", endpoint)

    # Device Settings
    async def get_night_light_setting(self, device_id: str) -> dict:
        """Get night light settings for a device."""
        device_data = await self.get_device_state(device_id)
        return device_data.get("night_light_setting", {})

    async def set_night_light_setting(
        self, device_id: str, brightness: int = None, 
        color: dict = None, auto: bool = None, on: bool = None
    ) -> dict:
        """Update night light settings."""
        current = await self.get_night_light_setting(device_id)
        payload = {
            "brightness": brightness if brightness is not None else current.get("brightness"),
            "color": color if color else current.get("color"),
            "auto": auto if auto is not None else current.get("auto"),
            "on": on if on is not None else current.get("on"),
        }
        # Use the working update endpoint
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json={"night_light_setting": payload})

    async def get_pilot_light_setting(self, device_id: str) -> dict:
        """Get pilot light settings for a device."""
        device_data = await self.get_device_state(device_id)
        return device_data.get("pilot_light_setting", {})

    async def set_pilot_light_setting(
        self, device_id: str, brightness: int = None,
        always_on: bool = None, auto_dim: bool = None, auto_dim_time: int = None
    ) -> dict:
        """Update pilot light settings."""
        current = await self.get_pilot_light_setting(device_id)
        payload = {
            "brightness": brightness if brightness is not None else current.get("brightness"),
            "always_on": always_on if always_on is not None else current.get("always_on"),
            "auto_dim": auto_dim if auto_dim is not None else current.get("auto_dim"),
            "auto_dim_time": auto_dim_time if auto_dim_time is not None else current.get("auto_dim_time"),
        }
        # Use the working update endpoint
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json={"pilot_light_setting": payload})

    async def get_display_setting(self, device_id: str) -> dict:
        """Get display settings for a device."""
        device_data = await self.get_device_state(device_id)
        return device_data.get("display_setting", {})

    async def set_display_setting(
        self, device_id: str, display_brightness: dict = None, timeout: dict = None
    ) -> dict:
        """Update display settings."""
        current = await self.get_display_setting(device_id)
        payload = {
            "display_brightness": display_brightness if display_brightness else current.get("display_brightness"),
            "timeout": timeout if timeout else current.get("timeout"),
        }
        # Use the working update endpoint
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json={"display_setting": payload})

    # Device Control Features
    # NOTE: These settings cannot be updated through the API.
    # The update-temperature endpoint rejects these fields with "is not allowed" error.
    # These settings appear to be read-only through the API and can only be changed
    # through the mobile app or device interface.
    
    async def set_child_lock(self, device_id: str, enabled: bool) -> dict:
        """Enable or disable child lock.
        
        NOTE: This setting cannot be changed through the API.
        The API endpoint rejects child_lock_setting with "is not allowed" error.
        This setting can only be changed through the mobile app.
        """
        raise EnviApiError(
            "Child lock setting cannot be changed through the API. "
            "Please use the Envi mobile app to change this setting."
        )

    async def set_freeze_protect(self, device_id: str, enabled: bool) -> dict:
        """Enable or disable freeze protection.
        
        NOTE: This setting cannot be changed through the API.
        The API endpoint rejects freeze_protect_setting with "is not allowed" error.
        This setting can only be changed through the mobile app.
        """
        raise EnviApiError(
            "Freeze protection setting cannot be changed through the API. "
            "Please use the Envi mobile app to change this setting."
        )

    async def set_notification_setting(self, device_id: str, enabled: bool) -> dict:
        """Enable or disable notifications.
        
        NOTE: This setting cannot be changed through the API.
        The API endpoint rejects notification_setting with "is not allowed" error.
        This setting can only be changed through the mobile app.
        """
        raise EnviApiError(
            "Notification setting cannot be changed through the API. "
            "Please use the Envi mobile app to change this setting."
        )

    async def set_hold(self, device_id: str, enabled: bool) -> dict:
        """Set temporary hold (prevents schedule changes).
        
        NOTE: This setting cannot be changed through the API.
        The API endpoint rejects is_hold with "is not allowed" error.
        This setting can only be changed through the mobile app.
        """
        raise EnviApiError(
            "Hold setting cannot be changed through the API. "
            "Please use the Envi mobile app to change this setting."
        )

    async def set_permanent_hold(self, device_id: str, enabled: bool) -> dict:
        """Set permanent hold (prevents all automatic changes).
        
        NOTE: This setting cannot be changed through the API.
        The API endpoint rejects permanent_hold with "is not allowed" error.
        This setting can only be changed through the mobile app.
        """
        raise EnviApiError(
            "Permanent hold setting cannot be changed through the API. "
            "Please use the Envi mobile app to change this setting."
        )

    # Utility Methods
    async def get_device_full_info(self, device_id: str) -> dict:
        """Get complete device information including all settings."""
        return await self.get_device_state(device_id)

    def convert_temperature(self, temperature: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature between Celsius and Fahrenheit."""
        if from_unit == to_unit:
            return temperature
        if from_unit.upper() == "C" and to_unit.upper() == "F":
            return (temperature * 9/5) + 32
        elif from_unit.upper() == "F" and to_unit.upper() == "C":
            return (temperature - 32) * 5/9
        return temperature

    async def test_connection(self) -> bool:
        """Test API connection."""
        try:
            await self.fetch_all_device_ids()
            return True
        except Exception:
            return False
