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
        self.token = None  # Initialize token attribute

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
                self.token = data.get('data', {}).get('token')  # Store token as an attribute
                return self.token
        except Exception as e:
            _LOGGER.error(f"Failed to authenticate with Envi API: {e}")
            return None

    async def fetch_external_device_id(self):
        """Fetch external device ID from the Envi API."""
        if not self.token:
            _LOGGER.error("Token is not available. Please authenticate first.")
            return None

        url = f"{self.base_url}/device/list"
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()  # Ensure HTTP request was successful
                data = await response.json()
                external_id = data['data'][0]['id']  # Adjust this according to the actual API response structure
                return external_id
        except Exception as e:
            _LOGGER.error(f"Failed to fetch external device ID: {e}")
            return None
    async def fetch_all_device_ids(self):
        """Fetch all device IDs from the Envi API and return them."""
        if not self.token:
            _LOGGER.error("Token is not available. Please authenticate first.")
            return None

        url = f"{self.base_url}/device/list"
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                device_ids = [device['id'] for device in data['data']]  # Extract all device IDs
                return device_ids
        except Exception as e:
            _LOGGER.error(f"Failed to fetch device IDs from Envi API: {e}")
            return None

    async def turn_on(self, device_id):
        url = f"{self.base_url}/device/update-temperature/{device_id}"
        headers = {'Authorization': f'Bearer {self.token}'}
        payload = {'state': 1}
        try:
            async with self.session.patch(url, headers=headers, json=payload) as response:
                response.raise_for_status()
        except Exception as e:
            _LOGGER.error(f"Failed to turn on device {device_id}: {e}")

    async def turn_off(self, device_id):
        url = f"{self.base_url}/device/update-temperature/{device_id}"
        headers = {'Authorization': f'Bearer {self.token}'}
        payload = {'state': 0}
        try:
            async with self.session.patch(url, headers=headers, json=payload) as response:
                response.raise_for_status()
        except Exception as e:
            _LOGGER.error(f"Failed to turn off device {device_id}: {e}")

    async def set_temperature(self, device_id, temperature):
        url = f"{self.base_url}/device/update-temperature/{device_id}"
        headers = {'Authorization': f'Bearer {self.token}'}
        payload = {'temperature': temperature}
        try:
            async with self.session.patch(url, headers=headers, json=payload) as response:
                response.raise_for_status()
        except Exception as e:
            _LOGGER.error(f"Failed to set temperature for device {device_id}: {e}")

    async def turn_off(self, device_id):
        url = f"{self.base_url}/device/update-temperature/{device_id}"
        headers = {'Authorization': f'Bearer {self.token}'}
        payload = {'state': 0}
        try:
            async with self.session.patch(url, headers=headers, json=payload) as response:
                response.raise_for_status()
        except Exception as e:
            _LOGGER.error(f"Failed to turn off device {device_id}: {e}")
    #Sample not used currently below
    async def refresh_token(self):
        """Refresh the API token."""
        url = f"{self.base_url}/auth/refresh-token"
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            async with self.session.post(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                self.token = data.get('data', {}).get('token')
                return self.token
        except Exception as e:
            _LOGGER.error(f"Failed to refresh token: {e}")
            return None
