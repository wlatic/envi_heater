from homeassistant.core import HomeAssistant
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import Platform

from .api import EnviApiClient
from .const import DOMAIN, CONF_DEVICE_ID
from .climate import EnviHeater

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Envi Heater component."""
    _LOGGER.info("Initializing Envi Heater component")
    return True

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """Set up Envi Heater from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create API client with device-specific ID
    session = async_get_clientsession(hass)
    api = EnviApiClient(
        session,
        entry.data['username'],
        entry.data['password'],
        entry.data[CONF_DEVICE_ID]  # Use stored device ID
    )
    
    # Store API client with device-specific data
    hass.data[DOMAIN][entry.entry_id] = {
        'api': api,
        'devices': {}
    }

    try:
        # Authenticate and get token
        token = await api.authenticate()
        if not token:
            _LOGGER.error("Failed to authenticate with Envi API")
            return False

        # Fetch all device IDs
        device_ids = await api.fetch_all_device_ids()
        if not device_ids:
            _LOGGER.error("Failed to fetch device IDs")
            return False

        # Create climate entities for each device
        devices = []
        for device_id in device_ids:
            # Store device-specific data
            hass.data[DOMAIN][entry.entry_id]['devices'][device_id] = {
                'api': api,
                'token': token,
                'external_id': device_id
            }
            
            # Create climate entity
            devices.append(EnviHeater(hass, entry, api, token, device_id))

        # Add all entities at once
        async_add_entities(devices)
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
