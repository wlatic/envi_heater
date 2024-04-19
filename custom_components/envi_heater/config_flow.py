import aiohttp
import uuid
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from .const import DOMAIN

class EnviHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Envi Heater."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user interface."""
        errors = {}

        if user_input is not None:
            # Retrieve or generate device_id
            store = Store(self.hass, version=1, key=f"{DOMAIN}_device_id")
            data = await store.async_load()
            if data and "device_id" in data:
                device_id = data["device_id"]
            else:
                device_id = uuid.uuid4().hex
                await store.async_save({"device_id": device_id})

            # Validate credentials
            valid = await self._test_credentials(user_input['username'], user_input['password'], device_id)
            
            if valid:
                # If valid, save and proceed with entry creation
                user_input['device_id'] = device_id
                return self.async_create_entry(title="Envi Heater", data=user_input)
            else:
                errors['base'] = 'auth'

        # Render the form again with errors (if any)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required('username', description={"suggested_value": "Your email"}): cv.string,
                vol.Required('password', description={"suggested_value": "Your password"}): cv.string
            }),
            errors=errors
        )

    async def _test_credentials(self, username, password, device_id):
        """Return True if credentials are valid, False otherwise."""
        try:
            # Create session using Home Assistant's aiohttp client session
            session = async_get_clientsession(self.hass)
            # Set up the payload for the post request
            payload = {
                "username": username,
                "password": password,
                "login_type": 1,
                "device_id": device_id,
                "device_type": "homeassistant"
            }
            # Make the authentication request to the Envi API
            async with session.post("https://app-apis.enviliving.com/apis/v1/auth/login", json=payload) as response:
                # Check if the response status code is OK
                if response.status == 200:
                    # Parse the JSON response
                    resp_json = await response.json()
                    # Check if the login was successful
                    return resp_json.get('status') == 'success' and 'token' in resp_json.get('data', {})
        except aiohttp.ClientError as error:
            # Log the error or handle it as appropriate
            pass

        # Return False if we reach this point without a successful login
        return False
