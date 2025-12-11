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

            # Use expires_in if present (it’s usually missing or wrong)
            expires_in = response_data["data"].get("expires_in")
            self.token_expires = datetime.now(timezone.utc) + timedelta(
                seconds=expires_in or 3600
            )

            # THIS IS THE FIX – parse real expiry from JWT (exactly like the working Hubitat version)
            jwt_expiry = self._parse_jwt_expiry(self.token)
            if jwt_expiry and jwt_expiry > self.token_expires:
                _LOGGER.info(
                    "Corrected token expiry using JWT: %s → %s (now once per year)",
                    self.token_expires.isoformat(timespec="minutes"),
                    jwt_expiry.isoformat(timespec="minutes"),
                )
                self.token_expires = jwt_expiry

            _LOGGER.debug("Authentication successful")
        except Exception as err:
            raise EnviAuthenticationError(f"Authentication failed: {err}") from err

    def _parse_jwt_expiry(self, token: str) -> datetime | None:
        """Extract the real 'exp' claim from the Envi JWT token."""
        try:
            payload_b64 = token.split(".")[1]
            payload_b64 += "=" * (-len(payload_b64) % 4)  # fix padding
            payload_json = base64.urlsafe_b64decode(payload_b64)
            claims = json.loads(payload_json)
            exp = claims.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, tz=timezone.utc)
        except Exception as exc:
            _LOGGER.debug("Could not parse JWT expiry (%s) — using expires_in value", exc)
        return None

    async def _is_token_valid(self) -> bool:
        """Check if current token is still valid (with 5-minute safety buffer)."""
        if not self.token or not self.token_expires:
            return False

        buffer_time = timedelta(minutes=5)
        is_valid = datetime.now(timezone.utc) < (self.token_expires - buffer_time)

        if not is_valid:
            _LOGGER.debug(
                "Token expired or expiring soon — Current: %s, Expires: %s",
                datetime.now(timezone.utc),
                self.token_expires,
            )
        return is_valid

     async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Perform API request with automatic token refresh on 401/403."""
        # If we have no token at all, authenticate first (but without holding the lock yet)
        if not self.token:
            await self.authenticate()

        headers = kwargs.setdefault("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        headers.setdefault("Accept", "application/json")

        url = f"{self.base_url}/{endpoint}"

        # Only use the lock for the actual HTTP request + possible single retry
        async with self._refresh_lock:
            try:
                async with self.session.request(
                    method.upper(), url, timeout=self.timeout, **kwargs
                ) as response:
                    if response.status in (401, 403):
                        # Token expired or invalid → refresh once and retry
                        _LOGGER.debug("Token invalid (%s), refreshing...", response.status)
                        await self.authenticate()

                        # Update header with new token and retry exactly once
                        headers["Authorization"] = f"Bearer {self.token}"
                        async with self.session.request(
                            method.upper(), url, timeout=self.timeout, headers=headers, **kwargs
                        ) as retry_response:
                            retry_response.raise_for_status()
                            return await retry_response.json()

                    response.raise_for_status()
                    return await response.json()

            except Exception as err:
                _LOGGER.error(f"API request failed ({method} {endpoint}): {err}")
                raise EnviDeviceError(f"API request failed: {err}") from err
    # Enhanced device methods with better error handling
    async def fetch_all_device_ids(self):
        """Get all device IDs from API."""
        try:
            data = await self._request("GET", "device/list")
            devices = data.get('data', [])
            if not devices:
                _LOGGER.warning("No devices found in account")
                return []
            return [device['id'] for device in devices]
        except EnviApiError:
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to fetch device IDs: {e}")
            raise EnviApiError(f"Failed to fetch devices: {e}")

    async def get_device_state(self, device_id):
        """Get current state of a device."""
        try:
            data = await self._request("GET", f"device/{device_id}")
            device_data = data.get('data', {})
            if not device_data:
                _LOGGER.warning(f"No data returned for device {device_id}")
                return {
                    "ambient_temperature": None,
                    "current_temperature": None,
                    "state": 0,
                }
            return device_data
        except EnviApiError:
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to get state for device {device_id}: {e}")
            raise EnviDeviceError(f"Failed to get device state: {e}")

    async def update_device(self, device_id, payload):
        """Generic update method for all device actions."""
        try:
            # Use the same endpoint for all updates - the original working approach
            endpoint = f"device/update-temperature/{device_id}"
                
            _LOGGER.debug(f"Updating device {device_id} via {endpoint} with payload: {payload}")
                
            result = await self._request("PATCH", endpoint, json=payload)
            _LOGGER.debug(f"Successfully updated device {device_id} with {payload}")
            return result
        except EnviApiError as e:
            _LOGGER.error(f"API error updating device {device_id}: {e}")
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to update device {device_id}: {e}")
            raise EnviDeviceError(f"Failed to update device: {e}")

    async def get_device_info(self, device_id):
        """Get detailed device information."""
        try:
            data = await self._request("GET", f"device/info/{device_id}")
            return data.get('data', {})
        except EnviApiError:
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to get info for device {device_id}: {e}")
            raise EnviDeviceError(f"Failed to get device info: {e}")

    async def test_connection(self):
        """Test the connection to the Envi API."""
        try:
            _LOGGER.debug("Testing connection to Envi API")
            # Try to get device list as a connection test
            device_ids = await self.fetch_all_device_ids()
            _LOGGER.debug(f"Connection test successful, found {len(device_ids)} devices")
            return True
        except EnviAuthenticationError as e:
            _LOGGER.error(f"Connection test failed - authentication error: {e}")
            return False
        except EnviApiError as e:
            _LOGGER.error(f"Connection test failed - API error: {e}")
            return False
        except Exception as e:
            _LOGGER.error(f"Connection test failed - unexpected error: {e}")
            return False
