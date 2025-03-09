import aiohttp
import asyncio
import logging
from aiohttp import ClientTimeout

_LOGGER = logging.getLogger(__name__)

class EnviApiClient:
    """Central API client with token management for all devices."""
    
    def __init__(self, session, username, password):
        self.session = session
        self.username = username
        self.password = password
        self.base_url = 'https://app-apis.enviliving.com/apis/v1'
        self.token = None
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
            async with self.session.post(url, json=payload, timeout=self.timeout) as resp:
                resp.raise_for_status()
                data = await resp.json()
                self.token = data.get('data', {}).get('token')
                return self.token
        except Exception as e:
            _LOGGER.error(f"Authentication failed: {e}")
            return None

    async def _request(self, method, endpoint, **kwargs):
        """Central API request handler with retries and token refresh."""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(3):  # 3 retries max
            try:
                # Auto-inject token if available
                headers = kwargs.get('headers', {})
                if self.token:
                    headers['Authorization'] = f'Bearer {self.token}'
                
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
                            _LOGGER.debug("Refreshing token...")
                            await self.authenticate()
                            continue
                            
                    resp.raise_for_status()
                    return await resp.json()
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < 2:  # Only log error on final attempt
                    _LOGGER.debug(f"Retrying {method} {endpoint}...")
                    await asyncio.sleep(1)
                else:
                    _LOGGER.error(f"API request failed: {e}")
                    raise

    # Simplified device methods
    async def fetch_all_device_ids(self):
        """Get all device IDs from API."""
        data = await self._request("GET", "device/list")
        return [device['id'] for device in data.get('data', [])]

    async def get_device_state(self, device_id):
        """Get current state of a device."""
        data = await self._request("GET", f"device/{device_id}")
        return data.get('data', {})

    async def update_device(self, device_id, payload):
        """Generic update method for all device actions."""
        return await self._request("PATCH", 
            f"device/update-temperature/{device_id}",
            json=payload
        )
