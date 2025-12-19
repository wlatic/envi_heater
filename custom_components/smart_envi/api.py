import asyncio
import base64
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

import aiohttp
from aiohttp import ClientError, ClientTimeout

from .const import (
    BASE_URL,
    ENDPOINTS,
    MAX_RETRIES,
    INITIAL_RETRY_DELAY,
    MAX_RETRY_DELAY,
)

_LOGGER = logging.getLogger(__name__)

# Retry configuration
RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)  # Rate limit and server errors
RETRYABLE_EXCEPTIONS = (aiohttp.ClientError, asyncio.TimeoutError)


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
    def __init__(
        self, 
        session: aiohttp.ClientSession, 
        username: str, 
        password: str,
        api_timeout: int = 15
    ):
        """Initialize Envi API client.
        
        Args:
            session: aiohttp session
            username: Envi account username
            password: Envi account password
            api_timeout: API request timeout in seconds (default: 15)
        """
        self.session = session
        self.username = username
        self.password = password
        self.base_url = BASE_URL
        self.token: str | None = None
        self.token_expires: datetime | None = None
        self._refresh_lock = asyncio.Lock()
        self.timeout = ClientTimeout(total=api_timeout)

    async def authenticate(self) -> None:
        """Authenticate with the Envi API and obtain an access token.
        
        Creates a unique device_id for each authentication attempt to avoid
        conflicts. The token expiration is parsed from the JWT token if available,
        otherwise defaults to 365 days.
        
        Raises:
            EnviAuthenticationError: If authentication fails (invalid credentials,
                network error, or API rejection)
        """
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
        _LOGGER.debug("Envi login attempt - device_id: %s", fresh_device_id)
        try:
            async with self.session.post(url, json=payload, headers=headers, timeout=self.timeout) as resp:
                resp_text = await resp.text()
                _LOGGER.debug("Envi login HTTP %s - %.1000s", resp.status, resp_text)
                if resp.status != 200:
                    raise EnviAuthenticationError(f"Login failed (HTTP {resp.status})")
                data = json.loads(resp_text)
                if data.get("status") != "success":
                    msg = data.get("msg", "unknown error")
                    raise EnviAuthenticationError(f"Envi rejected login: {msg}")
                self.token = data["data"]["token"]
                jwt_exp = self._parse_jwt_expiry(self.token)
                self.token_expires = jwt_exp or (datetime.now(timezone.utc) + timedelta(hours=24))
                _LOGGER.info(
                    "Envi login successful - token valid until %s",
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

    def _validate_response(self, data: dict, endpoint: str) -> None:
        """Validate API response structure.
        
        Args:
            data: Response data dictionary
            endpoint: API endpoint name for error context
            
        Raises:
            EnviApiError: If response structure is invalid
        """
        if not isinstance(data, dict):
            raise EnviApiError(f"Invalid response format from {endpoint}: expected dict, got {type(data).__name__}")
        
        # For device list endpoint, check for 'data' key
        if "device/list" in endpoint:
            if "data" not in data:
                _LOGGER.warning("Device list response missing 'data' key: %s", data.keys())
        
        # For device endpoints, check for 'data' key
        if endpoint.startswith("device/") and not endpoint.endswith("/list"):
            if "data" not in data:
                _LOGGER.warning("Device response missing 'data' key: %s", data.keys())

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Internal request with automatic token refresh, retry logic, and error handling.
        
        Implements:
        - Automatic token refresh
        - Retry with exponential backoff for transient errors
        - Rate limiting protection (429 handling)
        - Comprehensive error handling
        """
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

        # Retry loop with exponential backoff
        last_exception = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with self.session.request(method.upper(), url, timeout=self.timeout, **kwargs) as resp:
                    # Handle authentication errors (always retry once)
                    if resp.status in (401, 403):
                        if attempt == 0:  # Only retry auth errors once
                            _LOGGER.info("Token expired - refreshing automatically")
                            async with self._refresh_lock:
                                await self.authenticate()
                                headers["Authorization"] = f"Bearer {self.token}"
                                kwargs["headers"] = headers
                            continue  # Retry the request
                        else:
                            _LOGGER.error("Authentication failed after retry")
                            raise EnviAuthenticationError("Authentication failed")
                    
                    # Handle rate limiting (429)
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", INITIAL_RETRY_DELAY * (2 ** attempt)))
                        if attempt < MAX_RETRIES:
                            _LOGGER.warning(
                                "Rate limited (429). Retrying after %s seconds (attempt %s/%s)",
                                retry_after, attempt + 1, MAX_RETRIES + 1
                            )
                            await asyncio.sleep(min(retry_after, MAX_RETRY_DELAY))
                            continue
                        else:
                            _LOGGER.error("Rate limited (429) - max retries exceeded")
                            raise EnviApiError("Rate limited - too many requests")
                    
                    # Handle server errors (retryable)
                    if resp.status in RETRYABLE_STATUS_CODES:
                        if attempt < MAX_RETRIES:
                            delay = min(INITIAL_RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                            _LOGGER.warning(
                                "Server error %s. Retrying after %s seconds (attempt %s/%s)",
                                resp.status, delay, attempt + 1, MAX_RETRIES + 1
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            _LOGGER.error("Server error %s - max retries exceeded", resp.status)
                            resp.raise_for_status()
                    
                    # Don't raise on 400 - we want to handle it ourselves
                    if resp.status == 400:
                        data = await resp.json()
                        msg = data.get("msg", "Bad Request")
                        msg_code = data.get("msgCode", "unknown")
                        _LOGGER.error("API returned 400 Bad Request: %s (code: %s). Payload may be invalid.", msg, msg_code)
                        raise EnviApiError(f"Bad Request: {msg} (code: {msg_code})")
                    
                    resp.raise_for_status()
                    data = await resp.json()
                    
                    # Validate response structure
                    self._validate_response(data, endpoint)
                    
                    # Check API-level success status (some endpoints may not use status field)
                    api_status = data.get("status")
                    if api_status is not None and api_status != "success":
                        msg = data.get("msg", "Unknown error")
                        msg_code = data.get("msgCode", "unknown")
                        _LOGGER.warning("API returned error: %s (code: %s)", msg, msg_code)
                        raise EnviApiError(f"API error: {msg} (code: {msg_code})")
                    
                    return data
                    
            except RETRYABLE_EXCEPTIONS as err:
                last_exception = err
                if attempt < MAX_RETRIES:
                    delay = min(INITIAL_RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                    _LOGGER.warning(
                        "Network error during API request: %s. Retrying after %s seconds (attempt %s/%s)",
                        err, delay, attempt + 1, MAX_RETRIES + 1
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    _LOGGER.error("Network error - max retries exceeded: %s", err)
                    raise EnviApiError(f"Network error: {err}") from err
            except json.JSONDecodeError as err:
                _LOGGER.error("Invalid JSON response from API: %s", err)
                raise EnviApiError("Invalid response from API") from err
        
        # If we exhausted retries, raise the last exception
        if last_exception:
            raise EnviApiError(f"Request failed after {MAX_RETRIES + 1} attempts: {last_exception}") from last_exception
        raise EnviApiError("Request failed - unknown error")

    async def fetch_all_device_ids(self) -> list[str]:
        """Fetch all device IDs with validation."""
        data = await self._request("GET", ENDPOINTS["device_list"])
        device_list = data.get("data", [])
        
        if not isinstance(device_list, list):
            _LOGGER.error("Invalid device list format: expected list, got %s", type(device_list).__name__)
            return []
        
        device_ids = []
        for device in device_list:
            if not isinstance(device, dict):
                _LOGGER.warning("Invalid device entry: expected dict, got %s", type(device).__name__)
                continue
            device_id = device.get("id")
            if device_id:
                device_ids.append(str(device_id))
            else:
                _LOGGER.warning("Device entry missing 'id' field: %s", device)
        
        return device_ids

    async def get_device_state(self, device_id: str) -> dict:
        """Get device state with validation."""
        endpoint = ENDPOINTS["device_get"].format(device_id=device_id)
        data = await self._request("GET", endpoint)
        device_data = data.get("data", {})
        
        if not isinstance(device_data, dict):
            _LOGGER.error("Invalid device data format for device %s: expected dict, got %s", device_id, type(device_data).__name__)
            return {}
        
        # Validate required fields
        if "id" not in device_data and "serial_no" not in device_data:
            _LOGGER.warning("Device data missing identifier fields: %s", list(device_data.keys()))
        
        return device_data

    async def update_device(self, device_id: str, payload: dict) -> dict:
        """Update device temperature and/or state."""
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json=payload)

    async def set_temperature(self, device_id: str, temperature: float) -> dict:
        """Set target temperature for a device.
        
        Args:
            device_id: Device identifier
            temperature: Target temperature in the device's configured unit
            
        Returns:
            API response dictionary
            
        Raises:
            EnviApiError: If the API request fails
            EnviDeviceError: If device-specific error occurs
        """
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json={"temperature": temperature})

    async def set_state(self, device_id: str, state: int) -> dict:
        """Set device state (on/off).
        
        Args:
            device_id: Device identifier
            state: Device state (1 = on, 0 = off)
            
        Returns:
            API response dictionary
            
        Raises:
            EnviApiError: If the API request fails
            EnviDeviceError: If device-specific error occurs
        """
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json={"state": state})

    async def set_mode(self, device_id: str, mode: int) -> dict:
        """Set device mode (1 = heat, 3 = auto, etc.)."""
        endpoint = ENDPOINTS["device_update"].format(device_id=device_id)
        return await self._request("PATCH", endpoint, json={"mode": mode})

    # Schedule Management
    async def get_schedule_list(self) -> list[dict]:
        """Get list of all schedules.
        
        Returns:
            List of schedule dictionaries, each containing:
            - id: Schedule ID
            - device_id: Associated device ID
            - name: Schedule name
            - enabled: Whether schedule is enabled
            - temperature: Target temperature
            - trigger_time: Time when schedule activates
            - day: Day of week (if applicable)
        """
        data = await self._request("GET", ENDPOINTS["schedule_list"])
        schedule_list = data.get("data", [])
        if not isinstance(schedule_list, list):
            _LOGGER.warning("Invalid schedule list format: expected list, got %s", type(schedule_list).__name__)
            return []
        return schedule_list

    async def get_schedule(self, schedule_id: int) -> dict:
        """Get a specific schedule by ID.
        
        Args:
            schedule_id: Schedule ID to retrieve
            
        Returns:
            Schedule dictionary with schedule details
            
        Raises:
            EnviDeviceError: If schedule is not found
        """
        schedules = await self.get_schedule_list()
        for schedule in schedules:
            if isinstance(schedule, dict) and schedule.get("id") == schedule_id:
                return schedule
        raise EnviDeviceError(f"Schedule {schedule_id} not found")

    async def create_schedule(self, schedule_data: dict) -> dict:
        """Create a new schedule.
        
        Args:
            schedule_data: Dictionary containing schedule configuration:
                - device_id: Device ID (required)
                - enabled: bool - Whether schedule is enabled
                - name: str (optional) - Schedule name
                - temperature: float - Target temperature
                - times: list (optional) - List of time entries
                
        Returns:
            API response dictionary with created schedule data
            
        Raises:
            EnviApiError: If schedule creation fails
        """
        if not isinstance(schedule_data, dict):
            raise EnviApiError("Schedule data must be a dictionary")
        
        if "device_id" not in schedule_data:
            raise EnviApiError("device_id is required for schedule creation")
        
        return await self._request("POST", ENDPOINTS["schedule_add"], json=schedule_data)

    async def update_schedule(self, schedule_id: int, schedule_data: dict) -> dict:
        """Update an existing schedule.
        
        Args:
            schedule_id: Schedule ID to update
            schedule_data: Dictionary containing schedule updates:
                - enabled: bool (optional) - Whether schedule is enabled
                - name: str (optional) - Schedule name
                - temperature: float (optional) - Target temperature
                - times: list (optional) - List of time entries
                
        Returns:
            API response dictionary with updated schedule data
            
        Raises:
            EnviApiError: If schedule update fails
            EnviDeviceError: If schedule is not found
        """
        if not isinstance(schedule_data, dict):
            raise EnviApiError("Schedule data must be a dictionary")
        
        endpoint = ENDPOINTS["schedule_update"].format(schedule_id=schedule_id)
        return await self._request("PUT", endpoint, json=schedule_data)

    async def delete_schedule(self, schedule_id: int) -> dict:
        """Delete a schedule.
        
        Args:
            schedule_id: Schedule ID to delete
            
        Returns:
            API response dictionary
            
        Raises:
            EnviApiError: If schedule deletion fails
            EnviDeviceError: If schedule is not found
        """
        endpoint = ENDPOINTS["schedule_delete"].format(schedule_id=schedule_id)
        return await self._request("DELETE", endpoint)

    # Device Settings
    async def get_night_light_setting(self, device_id: str) -> dict:
        """Get night light settings for a device."""
        device_data = await self.get_device_state(device_id)
        return device_data.get("night_light_setting", {})

    async def set_night_light_setting(
        self, device_id: str, brightness: int | None = None, 
        color: dict | None = None, auto: bool | None = None, on: bool | None = None
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
        self, device_id: str, brightness: int | None = None,
        always_on: bool | None = None, auto_dim: bool | None = None, auto_dim_time: int | None = None
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
        self, device_id: str, display_brightness: dict | None = None, timeout: dict | None = None
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
        """Convert temperature between Celsius and Fahrenheit.
        
        Args:
            temperature: Temperature value to convert
            from_unit: Source unit ("C" or "F")
            to_unit: Target unit ("C" or "F")
            
        Returns:
            Converted temperature value
            
        Raises:
            ValueError: If from_unit or to_unit is not "C" or "F"
        """
        # Validate and normalize unit strings
        from_unit_upper = from_unit.upper().strip()
        to_unit_upper = to_unit.upper().strip()
        
        valid_units = {"C", "F"}
        if from_unit_upper not in valid_units:
            raise ValueError(f"Invalid source unit '{from_unit}'. Must be 'C' or 'F'")
        if to_unit_upper not in valid_units:
            raise ValueError(f"Invalid target unit '{to_unit}'. Must be 'C' or 'F'")
        
        # No conversion needed
        if from_unit_upper == to_unit_upper:
            return temperature
        
        # Perform conversion
        if from_unit_upper == "C" and to_unit_upper == "F":
            return (temperature * 9/5) + 32
        else:  # from_unit_upper == "F" and to_unit_upper == "C"
            return (temperature - 32) * 5/9

    async def test_connection(self) -> bool:
        """Test API connection."""
        try:
            await self.fetch_all_device_ids()
            return True
        except Exception:
            return False
