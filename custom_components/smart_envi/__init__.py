"""Smart Envi integration.

⚠️ UNOFFICIAL INTEGRATION: This integration is not created, maintained, or endorsed
by EHEAT, Inc. or Envi. It uses the Envi API in an unofficial capacity.

Smart Envi heaters manufactured by EHEAT, Inc. (https://www.eheat.com/)
Originally created by @wlatic (https://github.com/wlatic)
Enhanced with coordinator, sensors, and binary sensors.
"""
from __future__ import annotations

import logging

from datetime import timedelta

from aiohttp import ClientTimeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnviApiClient, EnviAuthenticationError
from .const import DOMAIN, SCAN_INTERVAL
from .coordinator import EnviDataUpdateCoordinator
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Envi from a config entry."""
    session = async_get_clientsession(hass)
    
    # Get options with defaults
    options = entry.options or {}
    api_timeout = options.get("api_timeout", 15)
    
    client = EnviApiClient(session, entry.data["username"], entry.data["password"], api_timeout=api_timeout)

    try:
        await client.authenticate()
    except EnviAuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client
    
    # Get scan interval from options or use default
    scan_interval_seconds = options.get("scan_interval", 30)
    scan_interval = timedelta(seconds=scan_interval_seconds)
    
    # Initialize coordinator with configurable scan interval
    coordinator = EnviDataUpdateCoordinator(hass, client, entry.entry_id, scan_interval)
    hass.data[DOMAIN][f"{DOMAIN}_coordinator_{entry.entry_id}"] = coordinator
    await coordinator.async_config_entry_first_refresh()
    
    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    # Set up services (only once)
    if DOMAIN not in hass.data or "services_setup" not in hass.data.get(DOMAIN, {}):
        await async_setup_services(hass)
        hass.data.setdefault(DOMAIN, {})["services_setup"] = True
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # Update API client timeout if changed
    options = entry.options or {}
    api_timeout = options.get("api_timeout", 15)
    
    client = hass.data[DOMAIN].get(entry.entry_id)
    if client:
        client.timeout = ClientTimeout(total=api_timeout)
    
    # Update coordinator scan interval if changed
    scan_interval_seconds = options.get("scan_interval", 30)
    scan_interval = timedelta(seconds=scan_interval_seconds)
    
    coordinator_key = f"{DOMAIN}_coordinator_{entry.entry_id}"
    coordinator = hass.data[DOMAIN].get(coordinator_key)
    if coordinator:
        coordinator.update_interval = scan_interval
        _LOGGER.info("Updated scan interval to %s seconds for entry %s", scan_interval_seconds, entry.entry_id)


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
