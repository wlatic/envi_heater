import logging
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .api import EnviApiError, EnviDeviceError, EnviAuthenticationError
from .coordinator import EnviDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Mode mapping
MODE_MAP = {
    1: "Heat",
    3: "Auto",
    # Add other modes as discovered
}


class EnviHeater(CoordinatorEntity, ClimateEntity):
    """Representation of an Envi Heater using centralized coordinator."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:radiator"  # Default icon, will update based on state
    _attr_entity_registry_enabled_default = True
    
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_from_coordinator()
        self.async_write_ha_state()
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_target_temperature_high = 86
    _attr_target_temperature_low = 50
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, coordinator: EnviDataUpdateCoordinator, device_id: str):
        """Initialize the heater."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.client = coordinator.client
        self.device_id = str(device_id)
        
        # Get initial device data from coordinator
        device_data = coordinator.get_device_data(device_id) or {}
        
        # Get device name from data if available
        device_name = device_data.get("name", f"Heater {device_id}")
        self._attr_name = device_name
        self._attr_unique_id = f"{DOMAIN}_{device_id}"
        
        # Temperature unit handling
        self._temperature_unit_api = device_data.get("temperature_unit", "F").upper()
        
        self._current_temperature = None
        self._target_temperature = None
        self._attr_hvac_mode = HVACMode.OFF
        self._serial_no = device_data.get("serial_no")
        self._firmware_version = device_data.get("firmware_version")
        self._model_no = device_data.get("model_no")
        
        # Update from coordinator data
        self._update_from_coordinator()

    def _update_from_coordinator(self):
        """Update entity state from coordinator data."""
        data = self.coordinator.get_device_data(self.device_id)
        if not data:
            return
        
        # Get temperature unit from device
        temp_unit = data.get("temperature_unit", "F").upper()
        self._temperature_unit_api = temp_unit
        
        # Get temperatures and convert if needed
        ambient_temp = data.get("ambient_temperature")
        target_temp = data.get("current_temperature")
        
        # Convert to Fahrenheit if device reports in Celsius
        if temp_unit == "C":
            if ambient_temp is not None:
                self._current_temperature = self.client.convert_temperature(ambient_temp, "C", "F")
            if target_temp is not None:
                self._target_temperature = self.client.convert_temperature(target_temp, "C", "F")
        else:
            self._current_temperature = ambient_temp
            self._target_temperature = target_temp
        
        # Update HVAC mode
        self._attr_hvac_mode = HVACMode.HEAT if data.get("state") == 1 else HVACMode.OFF
        
        # Update icon based on state
        if self._attr_hvac_mode == HVACMode.HEAT:
            self._attr_icon = "mdi:radiator"
        else:
            self._attr_icon = "mdi:radiator-off"
        
        # Update device info
        self._firmware_version = data.get("firmware_version")
        self._model_no = data.get("model_no")
        self._serial_no = data.get("serial_no", self._serial_no)
        
        # Update name if it changed
        if data.get("name") and data.get("name") != self._attr_name:
            self._attr_name = data.get("name")
        
        # Update extra state attributes with additional device information
        self._update_extra_attributes(data)

    def _update_extra_attributes(self, data: dict) -> None:
        """Update extra state attributes with device information."""
        schedule = data.get("schedule", {})
        schedule_name = None
        schedule_temp = None
        if isinstance(schedule, dict):
            schedule_name = schedule.get("name") or schedule.get("title")
            schedule_temp = schedule.get("temperature")
        
        self._attr_extra_state_attributes = {
            "signal_strength": data.get("signal_strength"),
            "wifi_ssid": data.get("ssid"),
            "location": data.get("location_name") or data.get("relative_location_name"),
            "firmware_version": data.get("firmware_version"),
            "model": data.get("model_no"),
            "serial_number": data.get("serial_no"),
            "mode": MODE_MAP.get(data.get("current_mode"), f"Mode {data.get('current_mode')}"),
            "mode_number": data.get("current_mode"),
            "temperature_unit": data.get("temperature_unit", "F"),
            "schedule_active": data.get("is_schedule_active", False),
            "schedule_name": schedule_name,
            "schedule_temperature": schedule_temp,
            "freeze_protect": not data.get("freeze_protect_setting", True),  # Inverted
            "child_lock": not data.get("child_lock_setting", True),  # Inverted
            "hold": data.get("is_hold", False),
            "geofence_active": data.get("is_geofence_active", False),
            "last_update": data.get("device_status_res_at") or data.get("device_status_req_at"),
        }

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.get_device_data(self.device_id) is not None

    @property
    def current_temperature(self):
        """Return current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return target temperature."""
        return self._target_temperature

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        model = self._model_no or "Smart Heater"
        if not model:
            model = "Smart Heater"
        
        # Build device name with location if available
        device_name = self._attr_name
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            location = data.get("location_name") or data.get("relative_location_name")
            if location and location not in device_name:
                device_name = f"{device_name} ({location})"
        
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.device_id))},
            name=device_name,
            manufacturer="Envi",
            model=model,
            sw_version=self._firmware_version or "Unknown",
            serial_number=self._serial_no,
            configuration_url="https://app.enviliving.com",
        )

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        
        # Convert to device's unit if needed
        if self._temperature_unit_api == "C":
            temp_to_send = self.client.convert_temperature(temperature, "F", "C")
        else:
            temp_to_send = temperature
            
        try:
            await self.client.set_temperature(self.device_id, temp_to_send)
            self._target_temperature = temperature  # Store in Fahrenheit for HA
            _LOGGER.debug("Set temperature to %s°F (%s°%s) for %s", 
                         temperature, temp_to_send, self._temperature_unit_api, self.device_id)
            # Refresh this device's data immediately
            await self.coordinator.async_refresh_device(self.device_id)
            self._update_from_coordinator()
        except EnviDeviceError as e:
            _LOGGER.error("Device error setting temperature: %s", e)
            raise
        except EnviApiError as e:
            _LOGGER.error("API error setting temperature: %s", e)
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error setting temperature: %s", e)
            raise

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        try:
            if hvac_mode == HVACMode.HEAT:
                _LOGGER.debug("Turning on heater %s", self.device_id)
                await self.client.set_state(self.device_id, 1)
                self._attr_hvac_mode = hvac_mode
                _LOGGER.debug("Turned on heater %s", self.device_id)
            else:
                _LOGGER.debug("Turning off heater %s", self.device_id)
                await self.client.set_state(self.device_id, 0)
                self._attr_hvac_mode = hvac_mode
                _LOGGER.debug("Turned off heater %s", self.device_id)
            # Refresh this device's data immediately
            await self.coordinator.async_refresh_device(self.device_id)
            self._update_from_coordinator()
        except EnviDeviceError as e:
            _LOGGER.error("Device error setting HVAC mode: %s", e)
            raise
        except EnviApiError as e:
            _LOGGER.error("API error setting HVAC mode: %s", e)
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error setting HVAC mode: %s", e)
            raise

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities
):
    """Set up all Envi heaters from a config entry."""
    client = hass.data[DOMAIN][entry.entry_id]
    
    # Get or create coordinator for this entry
    coordinator_key = f"{DOMAIN}_coordinator_{entry.entry_id}"
    if coordinator_key not in hass.data[DOMAIN]:
        coordinator = EnviDataUpdateCoordinator(hass, client, entry.entry_id)
        hass.data[DOMAIN][coordinator_key] = coordinator
        # Start initial data fetch
        await coordinator.async_config_entry_first_refresh()
    else:
        coordinator = hass.data[DOMAIN][coordinator_key]
    
    # Get device IDs from coordinator
    device_ids = coordinator.device_ids
    if not device_ids:
        _LOGGER.warning("No devices found for entry %s", entry.entry_id)
        return

    _LOGGER.info("Found %s Envi heaters: %s", len(device_ids), device_ids)
    
    # Create entities using coordinator
    heaters = [EnviHeater(coordinator, device_id) for device_id in device_ids]
    
    _LOGGER.info("Created %s heater entities", len(heaters))
    async_add_entities(heaters)
