"""Envi Heater integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .api import EnviApiClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Envi Heater from a config entry."""
    client = EnviApiClient(
        hass.helpers.aiohttp_client.async_get_clientsession(),
        entry.data["username"],
        entry.data["password"],
    )

    # Try to login
    try:
        await client.authenticate()
    except Exception as err:
        _LOGGER.error("Envi authentication failed: %s", err)
        raise ConfigEntryAuthFailed("Authentication failed") from err

    # Try to fetch devices – if this fails it’s usually network or API change
    try:
        device_ids = await client.fetch_all_device_ids()
        if not device_ids:
            _LOGGER.warning("Login succeeded but no devices found – possible account issue")
    except Exception as err:
        _LOGGER.error("Failed to fetch devices after successful login: %s", err)
        raise ConfigEntryNotReady("Could not fetch devices") from err

    hass.data.setdefault("envi_heater", {})[entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
