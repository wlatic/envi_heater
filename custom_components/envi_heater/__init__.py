"""Envi Heater integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryAuthFailed

from .api import EnviApiClient, EnviAuthenticationError

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Envi Heater from a config entry."""
    session = async_get_clientsession(hass)

    client = EnviApiClient(
        session=session,
        username=entry.data["username"],
        password=entry.data["password"],
    )

    # Re-auth to ensure token is fresh and creds still valid
    try:
        await client.authenticate()
    except EnviAuthenticationError as err:
        _LOGGER.error("Invalid credentials for Envi account: %s", err)
        # Triggers HA reauth flow (shows as invalid_auth)
        raise ConfigEntryAuthFailed("Invalid Envi credentials") from err
    except Exception as err:
        _LOGGER.error("Cannot connect to Envi API: %s", err)
        # Marks entry as not ready; HA will retry setup later
        raise ConfigEntryNotReady("Temporary Envi API error") from err

    hass.data.setdefault("envi_heater", {})[entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data["envi_heater"].pop(entry.entry_id, None)
    return unloaded
