"""DataUpdateCoordinator for Envi Heater integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EnviApiClient, EnviApiError, EnviAuthenticationError, EnviDeviceError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Update interval: 30 seconds (balance between responsiveness and API load)
SCAN_INTERVAL = timedelta(seconds=30)


class EnviDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Envi device data."""

    def __init__(self, hass: HomeAssistant, client: EnviApiClient, entry_id: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client
        self.entry_id = entry_id
        self.device_data: dict[str, dict] = {}
        self.device_ids: list[str] = []

    async def _async_update_data(self) -> dict[str, dict]:
        """Fetch data from Envi API.

        Returns:
            Dictionary mapping device_id to device data
        """
        try:
            # Always fetch device IDs first to handle new devices
            device_ids = await self.client.fetch_all_device_ids()
            _LOGGER.debug("Fetched %s device IDs: %s", len(device_ids), device_ids)
            
            # Update device_ids list
            self.device_ids = device_ids

            # Fetch data for all devices in parallel using asyncio.gather
            device_data = {}
            tasks = []
            for device_id in device_ids:
                tasks.append(self._fetch_device_data_safe(device_id))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, device_id in enumerate(device_ids):
                result = results[i]
                if isinstance(result, Exception):
                    _LOGGER.warning("Error fetching device %s: %s", device_id, result)
                    # Keep previous data if available
                    if str(device_id) in self.device_data:
                        device_data[str(device_id)] = self.device_data[str(device_id)]
                else:
                    device_data[str(device_id)] = result

            # Store the data
            self.device_data = device_data

            if not device_data:
                raise UpdateFailed("No device data available")

            return device_data

        except EnviAuthenticationError as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except EnviApiError as err:
            _LOGGER.error("API error during update: %s", err)
            raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error during update: %s", err, exc_info=True)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_refresh_device(self, device_id: str) -> dict | None:
        """Manually refresh a specific device."""
        try:
            data = await self.client.get_device_state(str(device_id))
            self.device_data[str(device_id)] = data
            # Notify listeners that this device's data changed
            self.async_update_listeners()
            return data
        except Exception as err:
            _LOGGER.error("Failed to refresh device %s: %s", device_id, err)
            return None

    async def _fetch_device_data_safe(self, device_id: str) -> dict:
        """Safely fetch device data with error handling."""
        try:
            data = await self.client.get_device_state(str(device_id))
            _LOGGER.debug("Fetched data for device %s: %s", device_id, data.get("name", "Unknown"))
            return data
        except EnviDeviceError as err:
            _LOGGER.warning("Device error for %s: %s", device_id, err)
            raise
        except Exception as err:
            _LOGGER.warning("Unexpected error fetching device %s: %s", device_id, err)
            raise

    def get_device_data(self, device_id: str) -> dict | None:
        """Get cached device data."""
        return self.device_data.get(str(device_id))

