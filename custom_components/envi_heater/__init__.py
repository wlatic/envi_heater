from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

from .api import EnviApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Envi Heater component."""
    return True  # No setup needed for YAML config

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Envi Heater from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize shared API client
    session = async_get_clientsession(hass)
    client = EnviApiClient(
        session=session,
        username=entry.data["username"],
        password=entry.data["password"]
    )

    # Authenticate and validate connection
    try:
        if not await client.authenticate():
            _LOGGER.error("Failed to authenticate with Envi API")
            return False
    except Exception as e:
        _LOGGER.error(f"Authentication error: {e}")
        return False

    # Verify we can get device IDs
    try:
        device_ids = await client.fetch_all_device_ids()
        if not device_ids:
            _LOGGER.error("No Envi devices found in account")
            return False
    except Exception as e:
        _LOGGER.error(f"Device ID fetch failed: {e}")
        return False

    # Store client in hass.data (single client per config entry)
    hass.data[DOMAIN][entry.entry_id] = client

    # Forward to climate platform using new method
    await hass.config_entries.async_forward_entry_setups(entry, ["climate"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # Clear client from memory
    hass.data[DOMAIN].pop(entry.entry_id)
    
    # Unload climate platform
    await hass.config_entries.async_forward_entry_unload(entry, "climate")
    return True
