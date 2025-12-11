"""Envi Heater integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .api import EnviApiClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Envi Heater from a config entry."""
    hass.data.setdefault("envi_heater", {})

    client = EnviApiClient(
        session=hass.helpers.aiohttp_client.async_get_clientsession(),
        username=entry.data["username"],
        password=entry.data["password"],
    )

    # Test login immediately – will raise if credentials/device_id bad
    try:
        await client.authenticate()
    except Exception as err:
        _LOGGER.error("Failed to authenticate during setup: %s", err)
        return False

    hass.data["envi_heater"][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data["envi_heater"].pop(entry.entry_id)
    return unload_ok
