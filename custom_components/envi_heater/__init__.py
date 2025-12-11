"""Envi Heater integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnviApiClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Envi Heater from a config entry."""
    client = EnviApiClient(
        session=async_get_clientsession(hass),   # ← correct way
        username=entry.data["username"],
        password=entry.data["password"],
    )

    # Login was already verified in config_flow, but do it again to be safe
    await client.authenticate()

    hass.data.setdefault("envi_heater", {})[entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
