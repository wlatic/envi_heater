"""Envi Heater integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnviApiClient, EnviAuthenticationError
from .const import DOMAIN
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Envi Heater from a config entry."""
    session = async_get_clientsession(hass)
    client = EnviApiClient(session, entry.data["username"], entry.data["password"])

    try:
        await client.authenticate()
    except EnviAuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client
    
    # Set up services (only once)
    if DOMAIN not in hass.data or "services_setup" not in hass.data.get(DOMAIN, {}):
        await async_setup_services(hass)
        hass.data.setdefault(DOMAIN, {})["services_setup"] = True
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Clean up coordinator
        coordinator_key = f"{DOMAIN}_coordinator_{entry.entry_id}"
        if coordinator_key in hass.data.get(DOMAIN, {}):
            hass.data[DOMAIN].pop(coordinator_key, None)
        # Clean up client
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)
    return unload_ok
