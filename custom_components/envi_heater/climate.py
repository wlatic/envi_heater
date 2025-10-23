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

_LOGGER = logging.getLogger(__name__)


class EnviHeater(ClimateEntity):
    """Representation of an Envi Heater using centralized API client."""

    _attr_has_entity_name = True
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
    _attr_should_poll = True  # Enable polling

    def __init__(self, hass, entry, client, device_id: str):
        """Initialize the heater."""
        self.hass = hass
        self.entry = entry
        self.client = client
        self.device_id = device_id
        self._attr_name = f"Envi Heater {device_id}"
        self._attr_unique_id = device_id  # Use device_id directly as unique_id
        self._current_temperature = None
        self._target_temperature = None
        self._attr_hvac_mode = HVACMode.OFF
        self._device_info = None
        self._attr_available = True

    @property
    def available(self):
        """Return if entity is available."""
        return self._attr_available

    @property
    def should_poll(self):
        """Return if polling is needed."""
        return True

    async def async_update(self):
        """Update device state from API."""
        try:
            data = await self.client.get_device_state(self.device_id)
            _LOGGER.debug(f"Updated device {self.device_id}: {data}")
            
            self._current_temperature = data.get("ambient_temperature")
            self._target_temperature = data.get("current_temperature")
            self._attr_hvac_mode = HVACMode.HEAT if data.get("state") == 1 else HVACMode.OFF
            self._attr_available = True
            
            _LOGGER.debug(f"Updated {self.device_id}: temp={self._current_temperature}, target={self._target_temperature}, mode={self._attr_hvac_mode}")
            
        except EnviAuthenticationError as e:
            self._attr_available = False
            _LOGGER.warning("Authentication failed for %s: %s", self.device_id, str(e))
        except EnviDeviceError as e:
            self._attr_available = False
            _LOGGER.warning("Device error for %s: %s", self.device_id, str(e))
        except Exception as e:
            self._attr_available = False
            _LOGGER.warning("Failed to update %s: %s", self.device_id, str(e))

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
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=self._attr_name,
            manufacturer="Envi",
            model="Smart Heater",
            sw_version="1.0",
        )

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
            
        try:
            await self.client.update_device(self.device_id, {"temperature": temperature})
            self._target_temperature = temperature
            _LOGGER.debug(f"Set temperature to {temperature}°F for {self.device_id}")
        except EnviDeviceError as e:
            _LOGGER.error(f"Device error setting temperature: {e}")
            raise
        except EnviApiError as e:
            _LOGGER.error(f"API error setting temperature: {e}")
            raise
        except Exception as e:
            _LOGGER.error(f"Unexpected error setting temperature: {e}")
            raise

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        try:
            if hvac_mode == HVACMode.HEAT:
                payload = {"state": 1}
                _LOGGER.debug(f"Turning on heater {self.device_id} with payload: {payload}")
                await self.client.update_device(self.device_id, payload)
                self._attr_hvac_mode = hvac_mode
                _LOGGER.debug(f"Turned on heater {self.device_id}")
            else:
                payload = {"state": 0}
                _LOGGER.debug(f"Turning off heater {self.device_id} with payload: {payload}")
                await self.client.update_device(self.device_id, payload)
                self._attr_hvac_mode = hvac_mode
                _LOGGER.debug(f"Turned off heater {self.device_id}")
        except EnviDeviceError as e:
            _LOGGER.error(f"Device error setting HVAC mode: {e}")
            raise
        except EnviApiError as e:
            _LOGGER.error(f"API error setting HVAC mode: {e}")
            raise
        except Exception as e:
            _LOGGER.error(f"Unexpected error setting HVAC mode: {e}")
            raise

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities
):
    """Set up all Envi heaters from a config entry."""
    client = hass.data[DOMAIN][entry.entry_id]
    
    try:
        device_ids = await client.fetch_all_device_ids()
    except Exception as e:
        _LOGGER.error("Failed to get device IDs: %s", str(e))
        return

    # Create entities directly without coordinator for now
    _LOGGER.info(f"Found {len(device_ids)} Envi heaters: {device_ids}")
    
    # Create entities
    heaters = [EnviHeater(hass, entry, client, device_id) for device_id in device_ids]
    _LOGGER.info(f"Created {len(heaters)} heater entities")
    async_add_entities(heaters)
    
    # Initial update for all heaters
    for heater in heaters:
        await heater.async_update()
