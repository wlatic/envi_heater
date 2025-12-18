"""DataUpdateCoordinator for Smart Envi integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EnviApiClient, EnviApiError, EnviAuthenticationError, EnviDeviceError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class EnviDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Envi device data."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        client: EnviApiClient, 
        entry_id: str,
        scan_interval: timedelta | None = None
    ) -> None:
        """Initialize the coordinator.
        
        Args:
            hass: Home Assistant instance
            client: Envi API client
            entry_id: Config entry ID
            scan_interval: Update interval (defaults to SCAN_INTERVAL constant)
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval or SCAN_INTERVAL,
        )
        self.client = client
        self.entry_id = entry_id
        self.device_data: dict[str, dict] = {}
        self.device_ids: list[str] = []

    async def _async_update_data(self) -> dict[str, dict]:
        """Fetch data from Envi API.

        This method fetches device IDs first, then fetches data for all devices
        in parallel. If some devices fail, it keeps cached data for those devices
        and only updates successful devices. This provides graceful degradation.

        Returns:
            Dictionary mapping device_id to device data
            
        Raises:
            UpdateFailed: If authentication fails, API errors occur, or no device
                data is available (even from cache)
        """
        try:
            # Always fetch device IDs first to handle new devices
            device_ids_raw = await self.client.fetch_all_device_ids()
            # Ensure all device IDs are strings
            device_ids = [str(did) for did in device_ids_raw]
            _LOGGER.debug("Fetched %s device IDs: %s", len(device_ids), device_ids)
            
            if not device_ids:
                # No devices found - keep existing data if available
                if self.device_data:
                    _LOGGER.warning("No devices found in account, keeping cached data")
                    return self.device_data
                raise UpdateFailed("No devices found in Envi account")
            
            # Update device_ids list
            self.device_ids = device_ids

            # Fetch data for all devices in parallel using asyncio.gather
            device_data = {}
            tasks = []
            for device_id in device_ids:
                tasks.append(self._fetch_device_data_safe(device_id))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle failures gracefully
            successful_updates = 0
            failed_devices = []
            for i, device_id in enumerate(device_ids):
                result = results[i]
                if isinstance(result, Exception):
                    failed_devices.append((device_id, str(result)))
                    _LOGGER.warning(
                        "Error fetching device %s: %s. Keeping cached data if available.",
                        device_id,
                        result,
                    )
                    # Keep previous data if available (graceful degradation)
                    if device_id in self.device_data:
                        device_data[device_id] = self.device_data[device_id]
                        _LOGGER.debug("Using cached data for device %s", device_id)
                    else:
                        _LOGGER.error(
                            "Device %s failed and no cached data available. "
                            "Device will appear unavailable.",
                            device_id,
                        )
                else:
                    device_data[device_id] = result
                    successful_updates += 1
            
            # Log summary
            if failed_devices:
                _LOGGER.warning(
                    "Update completed with %s successful and %s failed devices",
                    successful_updates,
                    len(failed_devices),
                )
            else:
                _LOGGER.debug("Successfully updated all %s devices", successful_updates)

            # Store the data
            self.device_data = device_data

            # Only fail if we have no data at all (not even cached)
            if not device_data:
                raise UpdateFailed(
                    "No device data available. All devices failed and no cached data exists."
                )

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
        """Manually refresh a specific device.
        
        This method fetches fresh data for a single device and updates the
        coordinator's cache. All entities listening to this coordinator will
        be notified of the update.
        
        Args:
            device_id: Device ID to refresh
            
        Returns:
            Updated device data dictionary, or None if refresh failed
        """
        device_id_str = str(device_id)
        try:
            data = await self.client.get_device_state(device_id_str)
            
            # Validate data
            if not data or not isinstance(data, dict):
                _LOGGER.warning("Invalid data received for device %s", device_id_str)
                return None
            
            self.device_data[device_id_str] = data
            # Notify listeners that this device's data changed
            self.async_update_listeners()
            _LOGGER.debug("Successfully refreshed device %s", device_id_str)
            return data
        except EnviAuthenticationError as err:
            _LOGGER.error("Authentication failed while refreshing device %s: %s", device_id_str, err)
            return None
        except EnviApiError as err:
            _LOGGER.error("API error refreshing device %s: %s", device_id_str, err)
            return None
        except Exception as err:
            _LOGGER.error("Unexpected error refreshing device %s: %s", device_id_str, err, exc_info=True)
            return None

    async def _fetch_device_data_safe(self, device_id: str) -> dict:
        """Safely fetch device data with error handling and validation.
        
        This method is used by the coordinator to fetch individual device data
        in parallel. Errors are caught and re-raised so the coordinator can
        handle them appropriately (keeping cached data for failed devices).
        
        Args:
            device_id: Device ID to fetch data for
            
        Returns:
            Device data dictionary
            
        Raises:
            EnviDeviceError: If device data is invalid or device-specific error occurs
            EnviApiError: If API error occurs (retries handled by API client)
            Exception: For unexpected errors
        """
        device_id_str = str(device_id)
        try:
            data = await self.client.get_device_state(device_id_str)
            
            # Validate we got meaningful data
            if not data or not isinstance(data, dict):
                _LOGGER.warning("Empty or invalid data for device %s", device_id_str)
                raise EnviDeviceError(f"Invalid data for device {device_id_str}")
            
            _LOGGER.debug("Fetched data for device %s: %s", device_id_str, data.get("name", "Unknown"))
            return data
        except EnviDeviceError as err:
            # Device-specific errors - don't retry, but log
            _LOGGER.warning("Device error for %s: %s", device_id_str, err)
            raise
        except EnviApiError as err:
            # API errors - may be transient, log but don't retry here (retry handled in API client)
            _LOGGER.warning("API error fetching device %s: %s", device_id_str, err)
            raise
        except Exception as err:
            # Unexpected errors - log with full context
            _LOGGER.warning("Unexpected error fetching device %s: %s", device_id_str, err, exc_info=True)
            raise

    def get_device_data(self, device_id: str) -> dict | None:
        """Get cached device data for a specific device.
        
        Args:
            device_id: Device ID to retrieve data for
            
        Returns:
            Cached device data dictionary, or None if device not found or not yet cached
        """
        return self.device_data.get(str(device_id))

