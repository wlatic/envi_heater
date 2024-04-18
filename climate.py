import logging
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT, HVAC_MODE_OFF
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Envi Heater climate entity from a config entry."""
    api = hass.data[DOMAIN][entry.entry_id]['api']
    async_add_entities([EnviHeater(hass, entry, api)])

class EnviHeater(ClimateEntity):
    """Representation of an Envi Heater."""
    def __init__(self, hass, entry, api):
        """Initialize the Envi Heater."""
        self.hass = hass
        self.entry = entry
        self.api = api
        self._current_temperature = None
        self._target_temperature = None
        self._hvac_mode = HVAC_MODE_OFF  # Starts as OFF
        self._available = True  # Track availability

    @property
    def name(self):
        """Return the name of the heater."""
        return f"Envi Heater {self.entry.data['device_id']}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.entry.data['device_id']

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, off."""
        return self._hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.api_set_temperature(temperature)

    async def async_update(self):
        """Fetch new state data for the heater."""
        await self.api_get_current_state()

    async def api_get_current_state(self):
        """Retrieve current state from the API."""
        url = f"https://app-apis.enviliving.com/apis/v1/device/{self.entry.data['device_id']}"
        headers = {'Authorization': f"Bearer {self.entry.data['token']}"}
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                self._current_temperature = data['data']['current_temperature']
                self._hvac_mode = HVAC_MODE_HEAT if data['data']['device_status'] == 1 else HVAC_MODE_OFF
                self._available = True
        except Exception as e:
            _LOGGER.error(f"An unexpected error occurred while fetching the state: {e}")
            self._available = False

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available
