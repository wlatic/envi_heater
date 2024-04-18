from homeassistant.core import HomeAssistant
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import Platform

from .api import EnviApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Envi Heater component."""
    _LOGGER.info("Initializing Envi Heater component")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Envi Heater from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})

    # Initialize API client
    session = async_get_clientsession(hass)
    client = EnviApiClient(session, entry.data['username'], entry.data['password'])
    hass.data[DOMAIN][entry.entry_id]['api'] = client  # Store API client immediately

    try:
        token = await client.authenticate()
        if not token:
            _LOGGER.error("Failed to authenticate with Envi API")
            return False

        # Fetch and store external IDs for all devices
        device_ids = await client.fetch_all_device_ids()
        if not device_ids:
            _LOGGER.error("Failed to fetch device IDs")
            return False

        # Store the token and external ID for each device
        for device_id in device_ids:
            # Initialize a dictionary for each device under its device_id
            hass.data[DOMAIN][entry.entry_id][device_id] = {
                'api': client, 
		'token': token,
                'external_id': device_id,
            }

        # Setup platforms like climate for each device
        for device_id in device_ids:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, Platform.CLIMATE)
            )

        return True
    except Exception as e:
        _LOGGER.error(f"Error setting up Envi Heater: {e}")
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # Remove the API client from hass.data
    hass.data[DOMAIN].pop(entry.entry_id, None)

    # Unload the climate platform
    return await hass.config_entries.async_forward_entry_unload(entry, Platform.CLIMATE)
