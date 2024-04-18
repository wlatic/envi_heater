import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class EnviApiClient:
    """Client to interact with the Envi Smart Heater API."""

    def __init__(self, session, username, password):
        self.session = session
        self.username = username
        self.password = password
        self.base_url = 'https://app-apis.enviliving.com/apis/v1'

    async def authenticate(self):
        """Authenticate with the Envi API and return a token."""
        url = f"{self.base_url}/auth/login"
        payload = {
            "username": self.username,
            "password": self.password,
            "login_type": 1,
            "device_id": "your_device_id",  # Ensure you handle the device ID appropriately
            "device_type": "homeassistant"
        }
        try:
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()  # Will throw an exception if the call failed
                data = await response.json()
                return data.get('data', {}).get('token')
        except Exception as e:
            _LOGGER.error(f"Failed to authenticate with Envi API: {e}")
            return None
