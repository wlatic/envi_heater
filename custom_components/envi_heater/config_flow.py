import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv
from .api import EnviApiClient
from .const import DOMAIN

class EnviHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Envi Heater config flow with modern auth handling."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial user-based config flow."""
        errors = {}
        
        if user_input is not None:
            # Validate credentials using API client
            session = async_get_clientsession(self.hass)
            client = EnviApiClient(
                session=session,
                username=user_input['username'],
                password=user_input['password']
            )

            try:
                # Test authentication and device access
                if not await client.authenticate():
                    errors["base"] = "invalid_auth"
                elif not await client.fetch_all_device_ids():
                    errors["base"] = "no_devices"
                else:
                    # Success - create entry without storing credentials
                    return self.async_create_entry(
                        title="Envi Heater",
                        data=user_input
                    )
            except Exception as e:
                _LOGGER.error("Config flow error: %s", str(e))
                errors["base"] = "connection_failed"

        # Show form with errors (if any)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("username"): cv.string,
                vol.Required("password"): cv.string
            }),
            errors=errors
        )
