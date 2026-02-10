"""Binary sensors for Smart Envi integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from .const import DOMAIN
from .coordinator import EnviDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class EnviBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for Envi binary sensors."""

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        sensor_type: str,
        device_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.device_id = str(device_id)
        self.sensor_type = sensor_type
        self._device_name = device_name
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{sensor_type}"
        self._attr_name = f"{device_name} {self._get_sensor_name()}"
    
    def _parse_inverted_bool(self, value, default_on: bool = True) -> bool:
        """Parse API boolean values with inverted semantics.
        
        API returns True when feature is OFF, False when ON.
        
        Args:
            value: API value (bool, int, str, or None)
            default_on: Default value if None or unexpected type
            
        Returns:
            Inverted boolean (True = feature ON, False = feature OFF)
        """
        if value is None:
            return default_on
        if isinstance(value, bool):
            return not value
        if isinstance(value, (int, str)):
            if value in (1, "true", "True", "1"):
                return False  # API True = OFF
            if value in (0, "false", "False", "0"):
                return True   # API False = ON
        return not bool(value)

    def _get_sensor_name(self) -> str:
        """Get human-readable sensor name."""
        names = {
            "freeze_protect": "Freeze Protection",
            "child_lock": "Child Lock",
            "schedule_active": "Schedule Active",
            "hold": "Hold",
            "online": "Online",
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
            return
        # Override in subclasses
        pass


class EnviFreezeProtectBinarySensor(EnviBinarySensor):
    """Binary sensor for freeze protection status."""

    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:snowflake-alert"

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize freeze protection sensor."""
        super().__init__(coordinator, device_id, "freeze_protect", device_name)

    def _update_from_coordinator(self) -> None:
        """Update freeze protection state."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            freeze_protect = data.get("freeze_protect_setting")
            # API returns inverted values: True=OFF, False=ON
            self._attr_is_on = self._parse_inverted_bool(freeze_protect, default_on=True)
            
            _LOGGER.debug(
                "Freeze protect for %s (%s): raw=%s (type=%s), is_on=%s (inverted)",
                self.device_id,
                self._device_name,
                freeze_protect,
                type(freeze_protect).__name__,
                self._attr_is_on
            )
            self._attr_available = True
        else:
            self._attr_available = False


class EnviChildLockBinarySensor(EnviBinarySensor):
    """Binary sensor for child lock status."""

    _attr_device_class = BinarySensorDeviceClass.LOCK
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize child lock sensor."""
        super().__init__(coordinator, device_id, "child_lock", device_name)

    def _update_from_coordinator(self) -> None:
        """Update child lock state."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            child_lock = data.get("child_lock_setting")
            # API returns inverted values: True=OFF, False=ON
            # Default to False (unlocked) if None
            self._attr_is_on = self._parse_inverted_bool(child_lock, default_on=False)
            
            _LOGGER.debug(
                "Child lock for %s (%s): raw=%s (type=%s), is_on=%s (inverted)",
                self.device_id,
                self._device_name,
                child_lock,
                type(child_lock).__name__,
                self._attr_is_on
            )
            self._attr_available = True
        else:
            self._attr_available = False


class EnviScheduleActiveBinarySensor(EnviBinarySensor):
    """Binary sensor for schedule active status."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:calendar-clock"

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize schedule active sensor."""
        super().__init__(coordinator, device_id, "schedule_active", device_name)

    def _update_from_coordinator(self) -> None:
        """Update schedule active state."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            self._attr_is_on = data.get("is_schedule_active", False)
            self._attr_available = True
        else:
            self._attr_available = False


class EnviHoldBinarySensor(EnviBinarySensor):
    """Binary sensor for hold status."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:pause-circle"

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize hold sensor."""
        super().__init__(coordinator, device_id, "hold", device_name)

    def _update_from_coordinator(self) -> None:
        """Update hold state."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            self._attr_is_on = data.get("is_hold", False)
            self._attr_available = True
        else:
            self._attr_available = False


class EnviOnlineBinarySensor(EnviBinarySensor):
    """Binary sensor for device online status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: EnviDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        """Initialize online sensor."""
        super().__init__(coordinator, device_id, "online", device_name)

    def _update_from_coordinator(self) -> None:
        """Update online state."""
        data = self.coordinator.get_device_data(self.device_id)
        if data:
            # Device is online if we have data and device_status is 1
            device_status = data.get("device_status", 0)
            self._attr_is_on = device_status == 1 and self.coordinator.last_update_success
            self._attr_available = True
        else:
            self._attr_is_on = False
            self._attr_available = False


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up Envi binary sensors from a config entry."""
    _LOGGER.debug("Setting up binary sensors for entry %s", entry.entry_id)
    
    # Get or create coordinator
    coordinator_key = f"{DOMAIN}_coordinator_{entry.entry_id}"
    
    # Get coordinator (should already be created in __init__.py)
    coordinator = hass.data.get(DOMAIN, {}).get(coordinator_key)
    if not coordinator:
        _LOGGER.error("Coordinator not found for entry %s", entry.entry_id)
        return
    
    device_ids = coordinator.device_ids

    if not device_ids:
        _LOGGER.warning("No devices found for entry %s after coordinator refresh", entry.entry_id)
        return

    _LOGGER.info("Found %s devices for binary sensors: %s", len(device_ids), device_ids)

    # Create binary sensors for each device
    binary_sensors = []
    for device_id in device_ids:
        try:
            device_data = coordinator.get_device_data(device_id) or {}
            device_name = device_data.get("name", f"Heater {device_id}")
            _LOGGER.debug("Creating binary sensors for device %s (%s)", device_id, device_name)

            # Create all binary sensors for this device
            binary_sensors.extend(
                [
                    EnviFreezeProtectBinarySensor(coordinator, device_id, device_name),
                    EnviChildLockBinarySensor(coordinator, device_id, device_name),
                    EnviScheduleActiveBinarySensor(coordinator, device_id, device_name),
                    EnviHoldBinarySensor(coordinator, device_id, device_name),
                    EnviOnlineBinarySensor(coordinator, device_id, device_name),
                ]
            )
        except Exception as e:
            _LOGGER.error("Error creating binary sensors for device %s: %s", device_id, e, exc_info=True)

    if not binary_sensors:
        _LOGGER.error("No binary sensors created!")
        return

    _LOGGER.info("Created %s binary sensors for %s devices", len(binary_sensors), len(device_ids))
    async_add_entities(binary_sensors, update_before_add=True)

