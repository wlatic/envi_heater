import logging
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

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

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client, device_id: str):
        """Initialize the heater."""
        self.hass = hass
        self.entry = entry
        self.client = client
        self.device_id = device_id
        self._attr_name = f"Envi Heater {device_id}"
        self._attr_unique_id = device_id
        self._attr_available = True
        self._current_temperature = None
        self._target_temperature = None
        self._attr_hvac_mode = HVACMode.OFF

    async def async_update(self):
        """Update device state from API."""
        try:
            data = await self.client.get_device_state(self.device_id)
            
            self._current_temperature = data.get("ambient_temperature")
            self._target_temperature = data.get("current_temperature")
            self._attr_hvac_mode = HVACMode.HEAT if data.get("state") == 1 else HVACMode.OFF
            self._attr_available = True
            
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

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
            
        try:
            await self.client.update_device(self.device_id, {"temperature": temperature})
            self._target_temperature = temperature
        except Exception as e:
            _LOGGER.error("Set temperature failed: %s", str(e))
            raise

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        try:
            if hvac_mode == HVACMode.HEAT:
                await self.client.update_device(self.device_id, {"state": 1})
            else:
                await self.client.update_device(self.device_id, {"state": 0})
            self._attr_hvac_mode = hvac_mode
        except Exception as e:
            _LOGGER.error("Set HVAC mode failed: %s", str(e))
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

    heaters = [EnviHeater(hass, entry, client, did) for did in device_ids]
    async_add_entities(heaters)
