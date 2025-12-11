import logging
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv

from .api import EnviApiClient, EnviAuthenticationError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class EnviHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Envi Heater config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle user-initiated flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input["username"]
            password = user_input["password"]

            session = async_get_clientsession(self.hass)
            client = EnviApiClient(
                session=session,
                username=username,
                password=password,
            )

            try:
                # 1) Test authentication – will raise EnviAuthenticationError on bad creds
                await client.authenticate()

                # 2) Verify device access
                device_ids = await client.fetch_all_device_ids()
                if not device_ids:
                    _LOGGER.warning(
                        "Envi login OK but no devices found for account %s", username
                    )
                    errors["base"] = "no_devices"
                else:
                    # 3) Success – store credentials and create entry
                    return self.async_create_entry(
                        title="Envi Heater",
                        data=user_input,
                    )

            except EnviAuthenticationError:
                _LOGGER.warning("Envi authentication failed for %s", username)
                errors["base"] = "invalid_auth"

            except aiohttp.ClientError:
                _LOGGER.warning("Cannot connect to Envi API for %s", username)
                errors["base"] = "cannot_connect"

            except Exception as e:
                _LOGGER.exception("Unexpected error during Envi config flow: %s", e)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): cv.string,
                    vol.Required("password"): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data):
        """Handle re-authentication."""
        # Simple re-use of user step, you could also prefill username here if you want
        return await self.async_step_user()
