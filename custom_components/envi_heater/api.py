import aiohttp
import asyncio
import logging
from aiohttp import ClientTimeout
from datetime import datetime, timedelta

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
    
    def __init__(self, session, username, password):
        self.session = session
        self.username = username
        self.password = password
        self.base_url = 'https://app-apis.enviliving.com/apis/v1'
        self.token = None
        self.token_expires = None
        self._refresh_lock = asyncio.Lock()  # Prevents concurrent token refreshes
        self.timeout = ClientTimeout(total=15)  # 15-second timeout

    async def authenticate(self):
        """Authenticate and get a fresh token."""
        url = f"{self.base_url}/auth/login"
        payload = {
            "username": self.username,
            "password": self.password,
            "login_type": 1,
            "device_id": "homeassistant_integration",
            "device_type": "homeassistant"
        }
        
        try:
            _LOGGER.debug("Attempting authentication with Envi API")
            async with self.session.post(url, json=payload, timeout=self.timeout) as resp:
                if resp.status == 401:
                    _LOGGER.error("Authentication failed: Invalid credentials")
                    raise EnviAuthenticationError("Invalid credentials")
                resp.raise_for_status()
                data = await resp.json()
                
                # Extract token and expiration from response
                token_data = data.get('data', {})
                self.token = token_data.get('token')
                
                if not self.token:
                    _LOGGER.error("No token received from API")
                    raise EnviAuthenticationError("No token received from API")
                
                # Try to get expiration from response, default to 1 hour
                expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
                self.token_expires = datetime.now() + timedelta(seconds=expires_in)
                
                _LOGGER.debug(f"Authentication successful, token expires at {self.token_expires}")
                return self.token
                
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Network error during authentication: {e}")
            raise EnviAuthenticationError(f"Network error during authentication: {e}")
        except Exception as e:
            _LOGGER.error(f"Authentication failed: {e}")
            raise EnviAuthenticationError(f"Authentication error: {e}")

    async def _is_token_valid(self):
        """Check if current token is still valid."""
        if not self.token or not self.token_expires:
            _LOGGER.debug("No token or expiration time available")
            return False
        
        # Add 5-minute buffer before expiration to prevent edge cases
        buffer_time = timedelta(minutes=5)
        is_valid = datetime.now() < (self.token_expires - buffer_time)
        
        if not is_valid:
            _LOGGER.debug(f"Token expired or will expire soon. Current time: {datetime.now()}, Token expires: {self.token_expires}")
        
        return is_valid

    async def _request(self, method, endpoint, **kwargs):
        """Central API request handler with retries and token refresh."""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(3):  # 3 retries max
            try:
                # Check if token needs refresh before request
                if not await self._is_token_valid():
                    async with self._refresh_lock:
                        if not await self._is_token_valid():  # Double-check after acquiring lock
                            _LOGGER.debug("Token expired, refreshing...")
                            await self.authenticate()
                
                # Auto-inject token if available
                headers = kwargs.get('headers', {})
                if self.token:
                    headers['Authorization'] = f'Bearer {self.token}'
                    _LOGGER.debug(f"Making {method} request to {endpoint} with token")
                else:
                    _LOGGER.warning(f"Making {method} request to {endpoint} without token")
                
                async with self.session.request(
                    method,
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    **kwargs
                ) as resp:
                    # Token expired - refresh and retry
                    if resp.status in (401, 403) and attempt < 2:
                        async with self._refresh_lock:
                            _LOGGER.warning(f"Token invalid (status {resp.status}), refreshing and retrying...")
                            await self.authenticate()
                            continue
                            
                    if resp.status >= 400:
                        error_text = await resp.text()
                        _LOGGER.error(f"API error {resp.status}: {error_text}")
                        if resp.status == 401:
                            raise EnviAuthenticationError("Authentication failed")
                        elif resp.status == 403:
                            raise EnviAuthenticationError("Unauthorized - token may be invalid")
                        elif resp.status >= 500:
                            raise EnviApiError(f"Server error: {resp.status}")
                        else:
                            raise EnviApiError(f"API error: {resp.status}")
                            
                    resp.raise_for_status()
                    return await resp.json()
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < 2:  # Only log error on final attempt
                    _LOGGER.debug(f"Retrying {method} {endpoint} (attempt {attempt + 1}) due to: {e}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    _LOGGER.error(f"API request failed after 3 attempts: {e}")
                    raise EnviApiError(f"Request failed: {e}")
            except EnviAuthenticationError:
                # Don't retry authentication errors
                raise

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
