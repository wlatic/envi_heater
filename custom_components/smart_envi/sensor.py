"""Sensors for Smart Envi integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from .const import DOMAIN
from .coordinator import EnviDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Mode mapping
MODE_MAP = {
    1: "Heat",
    3: "Auto",
    # Add other modes as discovered
}


class EnviSensor(CoordinatorEntity, SensorEntity):
    """Base class for Envi sensors."""

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        sensor_type: str,
        device_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.device_id = str(device_id)
        self.sensor_type = sensor_type
        self._device_name = device_name
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{sensor_type}"
        self._attr_name = f"{device_name} {self._get_sensor_name()}"
        
        # Try to set initial unit for schedule temperature sensor
        if sensor_type == "schedule_temperature":
            initial_data = coordinator.get_device_data(device_id)
            if initial_data:
                temp_unit = initial_data.get("temperature_unit", "F").upper()
                if temp_unit == "C":
                    self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
                else:
                    self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT

    def _get_sensor_name(self) -> str:
        """Get human-readable sensor name."""
        names = {
            "signal_strength": "Signal Strength",
            "firmware_version": "Firmware Version",
            "mode": "Mode",
            "schedule_name": "Schedule Name",
            "schedule_temperature": "Schedule Temperature",
            "wifi_ssid": "WiFi Network",
            "location": "Location",
            "model": "Model",
            "serial": "Serial Number",
            "last_update": "Last Update",
        }
        return names.get(self.sensor_type, self.sensor_type.replace("_", " ").title())

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=self._device_name,
            manufacturer="EHEAT",
        )

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_from_coordinator()
        self.async_write_ha_state()

    def _update_from_coordinator(self) -> None:
        """Update sensor state from coordinator data."""
        data = self.coordinator.get_device_data(self.device_id)
        if not data:
            self._attr_available = False
            return
        # Override in subclasses
        self._attr_available = True


class EnviSignalStrengthSensor(EnviSensor):
    """Sensor for WiFi signal strength."""

    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:signal"  # Will be dynamic based on strength

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize signal strength sensor."""
        super().__init__(coordinator, device_id, "signal_strength", device_name)

    def _update_from_coordinator(self) -> None:
        """Update signal strength."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            signal_strength = data.get("signal_strength")
            if signal_strength is not None:
                self._attr_native_value = int(signal_strength)
            else:
                self._attr_native_value = None
            self._attr_available = True
        else:
            self._attr_available = False


class EnviFirmwareVersionSensor(EnviSensor):
    """Sensor for firmware version."""

    _attr_icon = "mdi:chip"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize firmware version sensor."""
        super().__init__(coordinator, device_id, "firmware_version", device_name)

    def _update_from_coordinator(self) -> None:
        """Update firmware version."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            firmware = data.get("firmware_version")
            self._attr_native_value = firmware or "Unknown"
            self._attr_available = True
        else:
            self._attr_available = False


class EnviModeSensor(EnviSensor):
    """Sensor for device mode."""

    _attr_icon = "mdi:thermostat"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize mode sensor."""
        super().__init__(coordinator, device_id, "mode", device_name)

    def _update_from_coordinator(self) -> None:
        """Update mode."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            mode = data.get("current_mode")
            if mode is not None:
                # Map mode number to human-readable name
                mode_name = MODE_MAP.get(mode, f"Mode {mode}")
                self._attr_native_value = mode_name
                # Store raw mode as attribute
                self._attr_extra_state_attributes = {"mode_number": mode}
            else:
                self._attr_native_value = "Unknown"
            self._attr_available = True
        else:
            self._attr_available = False


class EnviScheduleNameSensor(EnviSensor):
    """Sensor for active schedule name."""

    _attr_icon = "mdi:calendar-clock"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize schedule name sensor."""
        super().__init__(coordinator, device_id, "schedule_name", device_name)

    def _update_from_coordinator(self) -> None:
        """Update schedule name."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            schedule = data.get("schedule", {})
            if isinstance(schedule, dict):
                schedule_name = schedule.get("name") or schedule.get("title")
                if schedule_name:
                    self._attr_native_value = schedule_name
                    # Add schedule details as attributes
                    self._attr_extra_state_attributes = {
                        "schedule_id": schedule.get("schedule_id"),
                        "temperature": schedule.get("temperature"),
                        "trigger_time": schedule.get("trigger_time"),
                        "day": schedule.get("day"),
                    }
                else:
                    self._attr_native_value = "None"
                    self._attr_extra_state_attributes = {}
            else:
                self._attr_native_value = "None"
                self._attr_extra_state_attributes = {}
            self._attr_available = True
        else:
            self._attr_available = False


class EnviScheduleTemperatureSensor(EnviSensor):
    """Sensor for scheduled temperature."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    # Note: Not using SensorDeviceClass.TEMPERATURE to prevent Home Assistant
    # from auto-converting to user's preferred unit. We want to show device's native unit.
    _attr_icon = "mdi:thermometer"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize schedule temperature sensor."""
        super().__init__(coordinator, device_id, "schedule_temperature", device_name)
        # Unit will be set based on device's temperature unit
        self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT  # Default, will be updated

    def _update_from_coordinator(self) -> None:
        """Update schedule temperature."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            schedule = data.get("schedule", {})
            temp_unit = data.get("temperature_unit", "F").upper()
            
            # Set unit of measurement based on device's unit
            # Use UnitOfTemperature constants to ensure proper handling
            if temp_unit == "C":
                self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            else:
                self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
            
            if isinstance(schedule, dict):
                temp = schedule.get("temperature")
                if temp is not None:
                    # Keep temperature in device's native unit (no conversion)
                    # The API already returns it in the correct unit
                    self._attr_native_value = float(temp)
                    _LOGGER.debug(
                        "Schedule temperature for %s: %s %s (device unit: %s, native_unit: %s)",
                        self.device_id,
                        self._attr_native_value,
                        self._attr_native_unit_of_measurement,
                        temp_unit,
                        self._attr_native_unit_of_measurement
                    )
                else:
                    self._attr_native_value = None
            else:
                self._attr_native_value = None
            self._attr_available = True
        else:
            self._attr_available = False


class EnviWiFiSSIDSensor(EnviSensor):
    """Sensor for WiFi SSID."""

    _attr_icon = "mdi:wifi"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize WiFi SSID sensor."""
        super().__init__(coordinator, device_id, "wifi_ssid", device_name)

    def _update_from_coordinator(self) -> None:
        """Update WiFi SSID."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            ssid = data.get("ssid")
            self._attr_native_value = ssid or "Unknown"
            self._attr_available = True
        else:
            self._attr_available = False


class EnviLocationSensor(EnviSensor):
    """Sensor for device location."""

    _attr_icon = "mdi:map-marker"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize location sensor."""
        super().__init__(coordinator, device_id, "location", device_name)

    def _update_from_coordinator(self) -> None:
        """Update location."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            location = data.get("location_name") or data.get("relative_location_name")
            self._attr_native_value = location or "Unknown"
            self._attr_available = True
        else:
            self._attr_available = False


class EnviModelSensor(EnviSensor):
    """Sensor for device model."""

    _attr_icon = "mdi:tag"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize model sensor."""
        super().__init__(coordinator, device_id, "model", device_name)

    def _update_from_coordinator(self) -> None:
        """Update model."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            model = data.get("model_no")
            self._attr_native_value = model or "Unknown"
            self._attr_available = True
        else:
            self._attr_available = False


class EnviSerialSensor(EnviSensor):
    """Sensor for device serial number."""

    _attr_icon = "mdi:barcode"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize serial sensor."""
        super().__init__(coordinator, device_id, "serial", device_name)

    def _update_from_coordinator(self) -> None:
        """Update serial number."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            serial = data.get("serial_no")
            self._attr_native_value = serial or "Unknown"
            self._attr_available = True
        else:
            self._attr_available = False


class EnviLastUpdateSensor(EnviSensor):
    """Sensor for last update timestamp."""

    _attr_icon = "mdi:clock-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize last update sensor."""
        super().__init__(coordinator, device_id, "last_update", device_name)

    def _update_from_coordinator(self) -> None:
        """Update last update timestamp."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            # Use device_status_res_at if available, otherwise device_status_req_at
            last_update = data.get("device_status_res_at") or data.get("device_status_req_at")
            if last_update:
                # Parse timestamp - must return datetime object for TIMESTAMP device class
                from datetime import datetime, timezone
                
                dt = None
                timestamp_str = str(last_update).strip()
                
                # Try multiple parsing strategies
                try:
                    # Try ISO format first (with or without Z)
                    if "Z" in timestamp_str:
                        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    elif "+" in timestamp_str or (timestamp_str.count("-") >= 3 and "T" in timestamp_str):
                        # Has timezone info (ISO format with timezone) or ISO format with T separator
                        dt = datetime.fromisoformat(timestamp_str)
                    else:
                        # Try common formats: "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DDTHH:MM:SS"
                        # This handles the format seen in the error: "2025-12-18 01:07:44"
                        for fmt in [
                            "%Y-%m-%d %H:%M:%S",
                            "%Y-%m-%dT%H:%M:%S",
                            "%Y-%m-%d %H:%M:%S.%f",
                            "%Y-%m-%dT%H:%M:%S.%f",
                        ]:
                            try:
                                dt = datetime.strptime(timestamp_str, fmt)
                                # Assume UTC if no timezone info
                                dt = dt.replace(tzinfo=timezone.utc)
                                break
                            except ValueError:
                                continue
                    
                    if dt is None:
                        raise ValueError(f"Could not parse timestamp: {timestamp_str}")
                    
                    # Ensure timezone-aware datetime
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    
                    # CRITICAL: For TIMESTAMP device class, Home Assistant expects a datetime object, not a string
                    # Double-check we're setting a datetime object, not a string
                    if not isinstance(dt, datetime):
                        raise TypeError(f"Expected datetime object, got {type(dt)}")
                    
                    self._attr_native_value = dt
                    _LOGGER.debug(
                        "Parsed timestamp '%s' to datetime %s for device %s",
                        timestamp_str,
                        dt,
                        self.device_id,
                    )
                except (ValueError, TypeError, AttributeError) as e:
                    # If parsing fails, set to None (not a string) for TIMESTAMP device class
                    _LOGGER.warning(
                        "Failed to parse timestamp '%s' (type: %s) for device %s: %s. Setting to None.",
                        timestamp_str,
                        type(last_update).__name__,
                        self.device_id,
                        e,
                    )
                    # CRITICAL: Must set None, not a string, for TIMESTAMP device class
                    self._attr_native_value = None
            else:
                # No timestamp available - set to None for TIMESTAMP device class
                self._attr_native_value = None
            self._attr_available = True
        else:
            self._attr_available = False


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up Envi sensors from a config entry."""
    _LOGGER.debug("Setting up sensors for entry %s", entry.entry_id)
    
    # Get or create coordinator
    coordinator_key = f"{DOMAIN}_coordinator_{entry.entry_id}"
    
    if coordinator_key not in hass.data.get(DOMAIN, {}):
        _LOGGER.warning("Coordinator not found, creating it for sensors")
        if entry.entry_id not in hass.data.get(DOMAIN, {}):
            _LOGGER.error("Client not found for entry %s", entry.entry_id)
            return
        
        client = hass.data[DOMAIN][entry.entry_id]
        from .coordinator import EnviDataUpdateCoordinator
        coordinator = EnviDataUpdateCoordinator(hass, client, entry.entry_id)
        hass.data.setdefault(DOMAIN, {})[coordinator_key] = coordinator
        try:
            await coordinator.async_config_entry_first_refresh()
        except Exception as e:
            _LOGGER.error("Failed to refresh coordinator: %s", e, exc_info=True)
            return
    else:
        coordinator = hass.data[DOMAIN][coordinator_key]
        _LOGGER.debug("Using existing coordinator")
    
    # Wait for coordinator to have device data if needed
    if not coordinator.device_ids:
        _LOGGER.debug("Coordinator has no device IDs yet, waiting for data...")
        if not coordinator.data:
            try:
                await coordinator.async_refresh()
            except Exception as e:
                _LOGGER.error("Failed to refresh coordinator: %s", e, exc_info=True)
                return
    
    device_ids = coordinator.device_ids

    if not device_ids:
        _LOGGER.warning("No devices found for entry %s after coordinator refresh", entry.entry_id)
        return

    _LOGGER.info("Found %s devices for sensors: %s", len(device_ids), device_ids)

    # Create sensors for each device
    sensors = []
    for device_id in device_ids:
        try:
            device_data = coordinator.get_device_data(device_id) or {}
            device_name = device_data.get("name", f"Heater {device_id}")
            _LOGGER.debug("Creating sensors for device %s (%s)", device_id, device_name)

            # Create all sensors for this device
            sensors.extend(
                [
                    EnviSignalStrengthSensor(coordinator, device_id, device_name),
                    EnviFirmwareVersionSensor(coordinator, device_id, device_name),
                    EnviModeSensor(coordinator, device_id, device_name),
                    EnviScheduleNameSensor(coordinator, device_id, device_name),
                    EnviScheduleTemperatureSensor(coordinator, device_id, device_name),
                    EnviWiFiSSIDSensor(coordinator, device_id, device_name),
                    EnviLocationSensor(coordinator, device_id, device_name),
                    EnviModelSensor(coordinator, device_id, device_name),
                    EnviSerialSensor(coordinator, device_id, device_name),
                    EnviLastUpdateSensor(coordinator, device_id, device_name),
                ]
            )
        except Exception as e:
            _LOGGER.error("Error creating sensors for device %s: %s", device_id, e, exc_info=True)

    if not sensors:
        _LOGGER.error("No sensors created!")
        return

    _LOGGER.info("Created %s sensors for %s devices", len(sensors), len(device_ids))
    async_add_entities(sensors, update_before_add=True)

