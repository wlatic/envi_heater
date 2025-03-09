import logging
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv

from .api import EnviApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class EnviHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Envi Heater config flow."""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle user-initiated flow."""
        errors = {}
        
        if user_input is not None:
            try:
                # Validate credentials
                session = async_get_clientsession(self.hass)
                client = EnviApiClient(
                    session=session,
                    username=user_input['username'],
                    password=user_input['password']
                )

                # Test authentication
                if not await client.authenticate():
                    errors["base"] = "invalid_auth"
                else:
                    # Verify device access
                    device_ids = await client.fetch_all_device_ids()
                    if not device_ids:
                        errors["base"] = "no_devices"
                    else:
                        return self.async_create_entry(
                            title="Envi Heater",
                            data=user_input
                        )
                        
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception("Unexpected error: %s", e)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("username"): cv.string,
                vol.Required("password"): cv.string
            }),
            errors=errors
        )

    async def async_step_reauth(self, entry_data):
        """Handle re-authentication."""
        return await self.async_step_user()
