"""Custom services for Smart Envi integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry
from homeassistant.const import ATTR_ENTITY_ID

from .const import DOMAIN
from .api import EnviApiClient, EnviApiError, EnviDeviceError

if TYPE_CHECKING:
    from .coordinator import EnviDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_device_id_from_entity(hass: HomeAssistant, entity_id: str) -> str | None:
    """Get device_id from entity using entity registry or fallback parsing.
    
    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to look up
        
    Returns:
        Device ID string or None if not found
    """
    try:
        # Try using entity registry first (preferred method)
        registry = entity_registry.async_get(hass)
        if registry_entry := registry.async_get(entity_id):
            unique_id = registry_entry.unique_id
            # Extract device_id from unique_id (format: "smart_envi_{device_id}")
            if unique_id.startswith(f"{DOMAIN}_"):
                return unique_id.replace(f"{DOMAIN}_", "", 1)
            return unique_id
    except Exception as e:
        _LOGGER.debug("Failed to get device_id from entity registry: %s", e)
    
    # Note: unique_id is only available from entity registry, not as a state attribute
    # No fallback needed as entity registry is the authoritative source
    return None


def _get_client_from_domain(hass: HomeAssistant) -> EnviApiClient | None:
    """Get the first available API client from domain data.
    
    Args:
        hass: Home Assistant instance
        
    Returns:
        EnviApiClient instance or None if not found
    """
    domain_data = hass.data.get(DOMAIN, {})
    for entry_id, client in domain_data.items():
        if entry_id != "services_setup" and isinstance(client, EnviApiClient):
            return client
    return None

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up custom services for Smart Envi integration."""
    
    async def refresh_all_heaters(call: ServiceCall) -> None:
        """Refresh all Smart Envi heaters."""
        _LOGGER.info("Refreshing all Smart Envi heaters")
        refreshed_count = 0
        failed_count = 0
        
        for entry_id in hass.data.get(DOMAIN, {}):
            if entry_id == "services_setup":
                continue
            try:
                coordinator_key = f"{DOMAIN}_coordinator_{entry_id}"
                coordinator = hass.data[DOMAIN].get(coordinator_key)
                if coordinator:
                    # Use coordinator to refresh all devices
                    await coordinator.async_refresh()
                    device_count = len(coordinator.device_ids)
                    refreshed_count += device_count
                    _LOGGER.info("Refreshed %s devices for entry %s", device_count, entry_id)
                else:
                    # Fallback to direct API calls if coordinator not available
                    client = hass.data[DOMAIN].get(entry_id)
                    if client:
                        device_ids = await client.fetch_all_device_ids()
                        for device_id in device_ids:
                            try:
                                await client.get_device_state(device_id)
                                refreshed_count += 1
                                _LOGGER.debug("Refreshed device %s", device_id)
                            except Exception as e:
                                failed_count += 1
                                _LOGGER.warning("Failed to refresh device %s: %s", device_id, e)
            except Exception as e:
                _LOGGER.error("Failed to refresh heaters for entry %s: %s", entry_id, e)
                failed_count += 1
        
        _LOGGER.info("Refresh complete: %s devices refreshed, %s failed", refreshed_count, failed_count)

    async def set_heater_schedule(call: ServiceCall) -> None:
        """Set a schedule for a Smart Envi heater.
        
        Schedule data structure:
        - enabled: bool - Whether the schedule is enabled
        - name: str (optional) - Schedule name
        - times: list (optional) - List of schedule times with temperature
          - time: str - Time in HH:MM:SS format
          - temperature: float - Target temperature (50-86°F)
          - enabled: bool - Whether this time slot is enabled
        
        Args:
            call: Service call with entity_id and schedule data
            
        Raises:
            HomeAssistantError: If entity_id is missing, device_id cannot be determined,
                API client is unavailable, or schedule data is invalid
        """
        entity_id = call.data.get(ATTR_ENTITY_ID)
        schedule_data = call.data.get("schedule", {})
        
        if not entity_id:
            raise HomeAssistantError("Entity ID is required")
        
        if not schedule_data:
            raise HomeAssistantError("Schedule data is required")
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            raise HomeAssistantError(f"Could not determine device_id for entity {entity_id}")
        
        client = _get_client_from_domain(hass)
        if not client:
            raise HomeAssistantError("Smart Envi integration not configured or API client unavailable")
        
        try:
            # Validate schedule data structure
            if not isinstance(schedule_data, dict):
                raise HomeAssistantError("Schedule data must be a dictionary")
            
            # Validate enabled field if present
            if "enabled" in schedule_data and not isinstance(schedule_data["enabled"], bool):
                raise HomeAssistantError("Schedule 'enabled' field must be a boolean")
            
            # Validate times if present
            if "times" in schedule_data:
                if not isinstance(schedule_data["times"], list):
                    raise HomeAssistantError("Schedule 'times' must be a list")
                for time_entry in schedule_data["times"]:
                    if not isinstance(time_entry, dict):
                        raise HomeAssistantError("Each schedule time entry must be a dictionary")
                    if "temperature" in time_entry:
                        temp = time_entry["temperature"]
                        if not isinstance(temp, (int, float)) or temp < 50 or temp > 86:
                            raise HomeAssistantError(
                                f"Schedule temperature must be between 50 and 86°F, got {temp}"
                            )
            
            # Get current device data to find schedule_id
            device_data = await client.get_device_state(device_id)
            schedule_info = device_data.get("schedule", {})
            schedule_id = None
            
            if isinstance(schedule_info, dict):
                schedule_id = schedule_info.get("schedule_id") or schedule_info.get("id")
            
            # Build schedule payload
            # Include device_id for creation, schedule_id for updates
            payload = schedule_data.copy()
            
            if schedule_id:
                # Update existing schedule
                _LOGGER.info("Updating schedule %s for device %s", schedule_id, device_id)
                _LOGGER.debug("Schedule update payload: %s", payload)
                await client.update_schedule(schedule_id, payload)
                _LOGGER.info("Schedule %s updated successfully for device %s", schedule_id, device_id)
            else:
                # Create new schedule
                _LOGGER.info("Creating new schedule for device %s", device_id)
                payload["device_id"] = device_id
                _LOGGER.debug("Schedule creation payload: %s", payload)
                await client.create_schedule(payload)
                _LOGGER.info("New schedule created successfully for device %s", device_id)
            
            # Refresh device data to get updated schedule info
            # Find the coordinator that manages this device
            domain_data = hass.data.get(DOMAIN, {})
            for entry_id, _ in domain_data.items():
                if entry_id == "services_setup":
                    continue
                coordinator_key = f"{DOMAIN}_coordinator_{entry_id}"
                coordinator = domain_data.get(coordinator_key)
                if coordinator and hasattr(coordinator, "async_refresh_device"):
                    # Check if this coordinator manages our device
                    if device_id in coordinator.device_ids:
                        await coordinator.async_refresh_device(device_id)
                        break
            
            _LOGGER.info("Schedule operation completed successfully for %s", entity_id)
        except HomeAssistantError:
            # Re-raise validation errors as-is
            raise
        except EnviApiError as e:
            _LOGGER.error("API error setting schedule for %s: %s", entity_id, e, exc_info=True)
            raise HomeAssistantError(f"Failed to set schedule: {e}") from e
        except Exception as e:
            _LOGGER.error("Unexpected error setting schedule for %s: %s", entity_id, e, exc_info=True)
            raise HomeAssistantError(f"Failed to set schedule: {str(e)}") from e

    async def get_heater_schedule(call: ServiceCall) -> dict:
        """Get the current schedule for a Smart Envi heater.
        
        Args:
            call: Service call with entity_id
            
        Returns:
            Dictionary containing schedule information:
            - schedule_id: Schedule ID (if exists)
            - enabled: Whether schedule is enabled
            - name: Schedule name
            - times: List of schedule time entries (if available)
            - device_id: Associated device ID
            
        Raises:
            HomeAssistantError: If entity_id is missing, device_id cannot be determined,
                API client is unavailable, or schedule retrieval fails
        """
        entity_id = call.data.get(ATTR_ENTITY_ID)
        
        if not entity_id:
            raise HomeAssistantError("Entity ID is required")
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            raise HomeAssistantError(f"Could not determine device_id for entity {entity_id}")
        
        client = _get_client_from_domain(hass)
        if not client:
            raise HomeAssistantError("Smart Envi integration not configured or API client unavailable")
        
        try:
            # Get device state to find schedule_id
            device_data = await client.get_device_state(device_id)
            schedule_info = device_data.get("schedule", {})
            
            schedule_id = None
            if isinstance(schedule_info, dict):
                schedule_id = schedule_info.get("schedule_id") or schedule_info.get("id")
            
            # If schedule_id exists, try to get full schedule details
            schedule_data = {
                "device_id": device_id,
                "schedule_id": schedule_id,
                "enabled": schedule_info.get("enabled", False) if isinstance(schedule_info, dict) else False,
                "name": schedule_info.get("name") or schedule_info.get("title") if isinstance(schedule_info, dict) else None,
                "temperature": schedule_info.get("temperature") if isinstance(schedule_info, dict) else None,
                "times": schedule_info.get("times", []) if isinstance(schedule_info, dict) else [],
            }
            
            # If we have a schedule_id, try to get more details from schedule list
            if schedule_id:
                try:
                    schedule_list = await client.get_schedule_list()
                    for schedule in schedule_list:
                        if isinstance(schedule, dict) and schedule.get("id") == schedule_id:
                            # Merge additional schedule details
                            schedule_data.update({
                                "enabled": schedule.get("enabled", schedule_data["enabled"]),
                                "name": schedule.get("name") or schedule_data["name"],
                                "temperature": schedule.get("temperature") or schedule_data["temperature"],
                                "times": schedule.get("times", schedule_data["times"]),
                                "trigger_time": schedule.get("trigger_time"),
                                "day": schedule.get("day"),
                            })
                            break
                except Exception as e:
                    _LOGGER.debug("Could not fetch full schedule details: %s", e)
                    # Continue with device state schedule info
            
            _LOGGER.info("Retrieved schedule for %s: %s", entity_id, schedule_data)
            return schedule_data
        except EnviApiError as e:
            _LOGGER.error("API error getting schedule for %s: %s", entity_id, e, exc_info=True)
            raise HomeAssistantError(f"Failed to get schedule: {e}") from e
        except Exception as e:
            _LOGGER.error("Failed to get schedule for %s: %s", entity_id, e, exc_info=True)
            raise HomeAssistantError(f"Failed to get schedule: {str(e)}") from e

    async def get_heater_status(call: ServiceCall) -> dict:
        """Get detailed status of a Smart Envi heater.
        
        Args:
            call: Service call with entity_id
            
        Returns:
            Dictionary containing device status information
            
        Raises:
            HomeAssistantError: If entity_id is missing, device_id cannot be determined,
                API client is unavailable, or status retrieval fails
        """
        entity_id = call.data.get(ATTR_ENTITY_ID)
        
        if not entity_id:
            raise HomeAssistantError("Entity ID is required")
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            raise HomeAssistantError(f"Could not determine device_id for entity {entity_id}")
        
        client = _get_client_from_domain(hass)
        if not client:
            raise HomeAssistantError("Smart Envi integration not configured or API client unavailable")
        
        try:
            # Get full device info
            device_info = await client.get_device_full_info(device_id)
            
            # Log detailed status
            _LOGGER.info("Retrieved status for %s (device_id: %s)", entity_id, device_id)
            _LOGGER.debug("=== Status for %s ===", entity_id)
            _LOGGER.debug("Device ID: %s", device_id)
            _LOGGER.debug("Name: %s", device_info.get("name"))
            _LOGGER.debug("Serial: %s", device_info.get("serial_no"))
            _LOGGER.debug("Model: %s", device_info.get("model_no"))
            _LOGGER.debug("Firmware: %s", device_info.get("firmware_version"))
            _LOGGER.debug("Current Temp: %s°%s", device_info.get("ambient_temperature"), device_info.get("temperature_unit", "F"))
            _LOGGER.debug("Target Temp: %s°%s", device_info.get("current_temperature"), device_info.get("temperature_unit", "F"))
            _LOGGER.debug("State: %s", "ON" if device_info.get("state") == 1 else "OFF")
            _LOGGER.debug("Mode: %s", device_info.get("current_mode"))
            _LOGGER.debug("Schedule Active: %s", device_info.get("is_schedule_active"))
            _LOGGER.debug("Freeze Protect: %s", device_info.get("freeze_protect_setting"))
            _LOGGER.debug("Signal Strength: %s%%", device_info.get("signal_strength"))
            
            # Return status as service result (for use in automations)
            return {
                "device_id": device_id,
                "name": device_info.get("name"),
                "current_temperature": device_info.get("ambient_temperature"),
                "target_temperature": device_info.get("current_temperature"),
                "state": "on" if device_info.get("state") == 1 else "off",
                "mode": device_info.get("current_mode"),
                "firmware_version": device_info.get("firmware_version"),
                "signal_strength": device_info.get("signal_strength"),
            }
        except EnviApiError as e:
            _LOGGER.error("API error getting status for %s: %s", entity_id, e, exc_info=True)
            raise HomeAssistantError(f"Failed to get device status: {e}") from e
        except Exception as e:
            _LOGGER.error("Failed to get status for %s: %s", entity_id, e, exc_info=True)
            raise HomeAssistantError(f"Failed to get device status: {str(e)}") from e

    async def test_connection(call: ServiceCall) -> None:
        """Test connection to Smart Envi API.
        
        Args:
            call: Service call (no parameters required)
            
        Raises:
            HomeAssistantError: If no API clients are found or connection test fails
        """
        _LOGGER.info("Testing connection to Smart Envi API")
        found_client = False
        for entry_id, client in hass.data.get(DOMAIN, {}).items():
            if entry_id == "services_setup" or not isinstance(client, EnviApiClient):
                continue
            found_client = True
            try:
                is_connected = await client.test_connection()
                if is_connected:
                    _LOGGER.info("Connection test successful for entry %s", entry_id)
                else:
                    raise HomeAssistantError(f"Connection test failed for entry {entry_id}")
            except HomeAssistantError:
                raise
            except Exception as e:
                _LOGGER.exception("Connection test error for entry %s", entry_id)
                raise HomeAssistantError(f"Connection test failed for entry {entry_id}: {e!s}") from e
        
        if not found_client:
            raise HomeAssistantError("No Smart Envi API clients found. Please configure the integration first.")


    async def set_freeze_protect(call: ServiceCall) -> None:
        """Enable or disable freeze protection.
        
        Note: This setting cannot be changed through the API and must be configured
        through the Envi mobile app. This service will raise an error if called.
        
        Args:
            call: Service call with entity_id and enabled flag
            
        Raises:
            HomeAssistantError: Always raised with explanation that this setting
                must be changed via the mobile app
        """
        entity_id = call.data.get(ATTR_ENTITY_ID)
        enabled = call.data.get("enabled", True)
        
        if not entity_id:
            raise HomeAssistantError("Entity ID is required")
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            raise HomeAssistantError(f"Could not determine device_id for entity {entity_id}")
        
        client = _get_client_from_domain(hass)
        if not client:
            raise HomeAssistantError("Smart Envi integration not configured or API client unavailable")
        
        try:
            await client.set_freeze_protect(device_id, enabled)
        except EnviApiError as e:
            # This will always raise since freeze protect cannot be changed via API
            raise HomeAssistantError(
                f"Freeze protection cannot be changed through Home Assistant. "
                f"Please use the Envi mobile app to modify this setting. "
                f"Original error: {e}"
            ) from e
        except Exception as e:
            _LOGGER.error("Failed to set freeze protection: %s", e, exc_info=True)
            raise HomeAssistantError(f"Failed to set freeze protection: {str(e)}") from e

    async def set_child_lock(call: ServiceCall) -> None:
        """Enable or disable child lock.
        
        Note: This setting cannot be changed through the API and must be configured
        through the Envi mobile app. This service will raise an error if called.
        
        Args:
            call: Service call with entity_id and enabled flag
            
        Raises:
            HomeAssistantError: Always raised with explanation that this setting
                must be changed via the mobile app
        """
        entity_id = call.data.get(ATTR_ENTITY_ID)
        enabled = call.data.get("enabled", True)
        
        if not entity_id:
            raise HomeAssistantError("Entity ID is required")
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            raise HomeAssistantError(f"Could not determine device_id for entity {entity_id}")
        
        client = _get_client_from_domain(hass)
        if not client:
            raise HomeAssistantError("Smart Envi integration not configured or API client unavailable")
        
        try:
            await client.set_child_lock(device_id, enabled)
        except EnviApiError as e:
            # This will always raise since child lock cannot be changed via API
            raise HomeAssistantError(
                f"Child lock cannot be changed through Home Assistant. "
                f"Please use the Envi mobile app to modify this setting. "
                f"Original error: {e}"
            ) from e
        except Exception as e:
            _LOGGER.error("Failed to set child lock: %s", e, exc_info=True)
            raise HomeAssistantError(f"Failed to set child lock: {str(e)}") from e

    async def set_hold(call: ServiceCall) -> None:
        """Set temporary hold (prevents schedule changes).
        
        Note: This setting cannot be changed through the API and must be configured
        through the Envi mobile app. This service will raise an error if called.
        
        Args:
            call: Service call with entity_id and enabled flag
            
        Raises:
            HomeAssistantError: Always raised with explanation that this setting
                must be changed via the mobile app
        """
        entity_id = call.data.get(ATTR_ENTITY_ID)
        enabled = call.data.get("enabled", True)
        
        if not entity_id:
            raise HomeAssistantError("Entity ID is required")
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            raise HomeAssistantError(f"Could not determine device_id for entity {entity_id}")
        
        client = _get_client_from_domain(hass)
        if not client:
            raise HomeAssistantError("Smart Envi integration not configured or API client unavailable")
        
        try:
            await client.set_hold(device_id, enabled)
        except EnviApiError as e:
            # This will always raise since hold cannot be changed via API
            raise HomeAssistantError(
                f"Hold setting cannot be changed through Home Assistant. "
                f"Please use the Envi mobile app to modify this setting. "
                f"Original error: {e}"
            ) from e
        except Exception as e:
            _LOGGER.error("Failed to set hold: %s", e, exc_info=True)
            raise HomeAssistantError(f"Failed to set hold: {str(e)}") from e

    # Register all services
    hass.services.async_register(
        DOMAIN,
        "refresh_all",
        refresh_all_heaters,
        schema=vol.Schema({}),
    )
    
    hass.services.async_register(
        DOMAIN,
        "set_schedule",
        set_heater_schedule,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
            vol.Required("schedule"): vol.Schema({
                vol.Required("enabled"): cv.boolean,
                vol.Optional("times"): vol.All(cv.ensure_list, [
                    vol.Schema({
                        vol.Required("time"): cv.time,
                        vol.Required("temperature"): vol.All(vol.Coerce(float), vol.Range(min=50, max=86)),
                        vol.Required("enabled"): cv.boolean,
                    })
                ])
            })
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        "get_schedule",
        get_heater_schedule,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        "get_status",
        get_heater_status,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        "test_connection",
        test_connection,
        schema=vol.Schema({}),
    )
    
    hass.services.async_register(
        DOMAIN,
        "set_freeze_protect",
        set_freeze_protect,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
            vol.Required("enabled"): cv.boolean,
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        "set_child_lock",
        set_child_lock,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
            vol.Required("enabled"): cv.boolean,
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        "set_hold",
        set_hold,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
            vol.Required("enabled"): cv.boolean,
        }),
    )

async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload custom services."""
    hass.services.async_remove(DOMAIN, "refresh_all")
    hass.services.async_remove(DOMAIN, "set_schedule")
    hass.services.async_remove(DOMAIN, "get_schedule")
    hass.services.async_remove(DOMAIN, "get_status")
    hass.services.async_remove(DOMAIN, "test_connection")
    hass.services.async_remove(DOMAIN, "set_freeze_protect")
    hass.services.async_remove(DOMAIN, "set_child_lock")
    hass.services.async_remove(DOMAIN, "set_hold")
