from homeassistant.core import HomeAssistant
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import Platform

from .api import EnviApiClient
from .const import DOMAIN
from .api import EnviApiClient  # Make sure to create an api.py with EnviApiClient

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up configured Envi Heater."""
    # This method is for setting up the component from configuration.yaml (if used).
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Envi Heater from a config entry."""
    # Initialize API client
    session = async_get_clientsession(hass)
    #client = EnviApiClient(session, entry.data['username'], entry.data['password'], entry.data.get('token'))
    client = EnviApiClient(session, entry.data['username'], entry.data['password'])
    # Authenticate with the Envi API
    token = await client.authenticate()

    if not token:
        _LOGGER.error("Failed to authenticate with Envi API")
        return False



    # Store API client in hass.data
    # Store both API client and token in hass.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        'api': client,
        'token': token
    }

    # Setup platforms like climate
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.CLIMATE)
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # Remove the API client from hass.data
    hass.data[DOMAIN].pop(entry.entry_id, None)

    # Unload the climate platform
    return await hass.config_entries.async_forward_entry_unload(entry, Platform.CLIMATE)
