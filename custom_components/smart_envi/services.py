import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry
from homeassistant.const import ATTR_ENTITY_ID

from .const import DOMAIN
from .api import EnviApiClient, EnviApiError, EnviDeviceError

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
    
    # Fallback to parsing entity state attributes
    try:
        entity = hass.states.get(entity_id)
        if entity:
            unique_id = entity.attributes.get("unique_id", "")
            if unique_id.startswith(f"{DOMAIN}_"):
                return unique_id.replace(f"{DOMAIN}_", "", 1)
            return unique_id if unique_id else None
    except Exception as e:
        _LOGGER.debug("Failed to get device_id from entity state: %s", e)
    
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
        """Set a schedule for a heater."""
        entity_id = call.data.get(ATTR_ENTITY_ID)
        schedule_data = call.data.get("schedule", {})
        
        if not entity_id:
            _LOGGER.error("No entity ID provided")
            return
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            _LOGGER.error("Could not determine device_id for entity %s", entity_id)
            return
        
        client = _get_client_from_domain(hass)
        if not client:
            _LOGGER.error("No Smart Envi API client found")
            return
        
        try:
            # Get current device data to find schedule_id
            device_data = await client.get_device_state(device_id)
            schedule_info = device_data.get("schedule", {})
            schedule_id = schedule_info.get("schedule_id") if isinstance(schedule_info, dict) else None
            
            # Build schedule payload (this may need adjustment based on actual API requirements)
            # For now, we'll try to create/update based on what we know
            if schedule_id:
                _LOGGER.info("Updating schedule %s for device %s", schedule_id, device_id)
                # Note: Actual payload structure needs to be determined from API
                await client.update_schedule(schedule_id, schedule_data)
            else:
                _LOGGER.info("Creating new schedule for device %s", device_id)
                schedule_data["device_id"] = device_id
                await client.create_schedule(schedule_data)
            
            _LOGGER.info("Schedule updated successfully for %s", entity_id)
        except EnviApiError as e:
            _LOGGER.error("Failed to set schedule for %s: %s", entity_id, e, exc_info=True)
            raise HomeAssistantError(f"Failed to set schedule: {e}") from e
        except Exception as e:
            _LOGGER.error("Failed to set schedule for %s: %s", entity_id, e, exc_info=True)
            raise HomeAssistantError(f"Failed to set schedule: {str(e)}") from e

    async def get_heater_status(call: ServiceCall) -> dict | None:
        """Get detailed status of a heater."""
        entity_id = call.data.get(ATTR_ENTITY_ID)
        
        if not entity_id:
            _LOGGER.error("No entity ID provided")
            return None
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            _LOGGER.error("Could not determine device_id for entity %s", entity_id)
            return None
        
        client = _get_client_from_domain(hass)
        if not client:
            _LOGGER.error("No Smart Envi API client found")
            return None
        
        try:
            # Get full device info
            device_info = await client.get_device_full_info(device_id)
            
            # Log detailed status
            _LOGGER.info("=== Status for %s ===", entity_id)
            _LOGGER.info("Device ID: %s", device_id)
            _LOGGER.info("Name: %s", device_info.get("name"))
            _LOGGER.info("Serial: %s", device_info.get("serial_no"))
            _LOGGER.info("Model: %s", device_info.get("model_no"))
            _LOGGER.info("Firmware: %s", device_info.get("firmware_version"))
            _LOGGER.info("Current Temp: %s°%s", device_info.get("ambient_temperature"), device_info.get("temperature_unit", "F"))
            _LOGGER.info("Target Temp: %s°%s", device_info.get("current_temperature"), device_info.get("temperature_unit", "F"))
            _LOGGER.info("State: %s", "ON" if device_info.get("state") == 1 else "OFF")
            _LOGGER.info("Mode: %s", device_info.get("current_mode"))
            _LOGGER.info("Schedule Active: %s", device_info.get("is_schedule_active"))
            _LOGGER.info("Freeze Protect: %s", device_info.get("freeze_protect_setting"))
            _LOGGER.info("Signal Strength: %s%%", device_info.get("signal_strength"))
            
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
        except Exception as e:
            _LOGGER.error("Failed to get status for %s: %s", entity_id, e, exc_info=True)
            return None

    async def test_connection(call: ServiceCall) -> None:
        """Test connection to Smart Envi API."""
        _LOGGER.info("Testing connection to Smart Envi API")
        for entry_id, client in hass.data[DOMAIN].items():
            if entry_id == "services_setup":
                continue
            try:
                is_connected = await client.test_connection()
                if is_connected:
                    _LOGGER.info("Connection test successful for entry %s", entry_id)
                else:
                    _LOGGER.error("Connection test failed for entry %s", entry_id)
            except Exception as e:
                _LOGGER.error("Connection test error for entry %s: %s", entry_id, e)


    async def set_freeze_protect(call: ServiceCall) -> None:
        """Enable or disable freeze protection."""
        entity_id = call.data.get(ATTR_ENTITY_ID)
        enabled = call.data.get("enabled", True)
        
        if not entity_id:
            _LOGGER.error("No entity ID provided")
            return
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            _LOGGER.error("Could not determine device_id for entity %s", entity_id)
            return
        
        client = _get_client_from_domain(hass)
        if not client:
            _LOGGER.error("No Smart Envi API client found")
            return
        
        try:
            await client.set_freeze_protect(device_id, enabled)
            _LOGGER.info("Freeze protection %s for %s", "enabled" if enabled else "disabled", entity_id)
        except EnviApiError as e:
            _LOGGER.error("Failed to set freeze protection: %s", e, exc_info=True)
            raise HomeAssistantError(f"Failed to set freeze protection: {e}") from e
        except Exception as e:
            _LOGGER.error("Failed to set freeze protection: %s", e, exc_info=True)
            raise HomeAssistantError(f"Failed to set freeze protection: {str(e)}") from e

    async def set_child_lock(call: ServiceCall) -> None:
        """Enable or disable child lock."""
        entity_id = call.data.get(ATTR_ENTITY_ID)
        enabled = call.data.get("enabled", True)
        
        if not entity_id:
            _LOGGER.error("No entity ID provided")
            return
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            _LOGGER.error("Could not determine device_id for entity %s", entity_id)
            return
        
        client = _get_client_from_domain(hass)
        if not client:
            _LOGGER.error("No Smart Envi API client found")
            return
        
        try:
            await client.set_child_lock(device_id, enabled)
            _LOGGER.info("Child lock %s for %s", "enabled" if enabled else "disabled", entity_id)
        except EnviApiError as e:
            _LOGGER.error("Failed to set child lock: %s", e, exc_info=True)
            raise HomeAssistantError(f"Failed to set child lock: {e}") from e
        except Exception as e:
            _LOGGER.error("Failed to set child lock: %s", e, exc_info=True)
            raise HomeAssistantError(f"Failed to set child lock: {str(e)}") from e

    async def set_hold(call: ServiceCall) -> None:
        """Set temporary hold (prevents schedule changes)."""
        entity_id = call.data.get(ATTR_ENTITY_ID)
        enabled = call.data.get("enabled", True)
        
        if not entity_id:
            _LOGGER.error("No entity ID provided")
            return
        
        device_id = _get_device_id_from_entity(hass, entity_id)
        if not device_id:
            _LOGGER.error("Could not determine device_id for entity %s", entity_id)
            return
        
        client = _get_client_from_domain(hass)
        if not client:
            _LOGGER.error("No Smart Envi API client found")
            return
        
        try:
            await client.set_hold(device_id, enabled)
            _LOGGER.info("Hold %s for %s", "enabled" if enabled else "disabled", entity_id)
        except EnviApiError as e:
            _LOGGER.error("Failed to set hold: %s", e, exc_info=True)
            raise HomeAssistantError(f"Failed to set hold: {e}") from e
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
    hass.services.async_remove(DOMAIN, "get_status")
    hass.services.async_remove(DOMAIN, "test_connection")
    hass.services.async_remove(DOMAIN, "set_freeze_protect")
    hass.services.async_remove(DOMAIN, "set_child_lock")
    hass.services.async_remove(DOMAIN, "set_hold")
