import logging
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Envi Heater climate entities from a config entry."""
    devices = []
    entry_data = hass.data[DOMAIN][entry.entry_id]

    # Ensure only dictionaries meant for devices are processed
    for device_id, device_info in entry_data.items():
        if isinstance(device_info, dict) and all(k in device_info for k in ['api', 'token', 'external_id']):
            api = device_info['api']
            token = device_info['token']
            external_id = device_info['external_id']
            devices.append(EnviHeater(hass, entry, api, token, external_id))

    async_add_entities(devices)

class EnviHeater(ClimateEntity):
    """Representation of an Envi Heater."""
    def __init__(self, hass, entry, api, token, external_id):
        """Initialize the Envi Heater."""
        self.hass = hass
        self.entry = entry
        self.api = api
        self.token = token
        self.external_id = external_id
        self._current_temperature = None
        self._target_temperature = None
        self._attr_hvac_mode = HVACMode.OFF  # Starts as OFF
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]  # Supported HVAC modes
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT  # Set the temperature unit
        self._attr_target_temperature_high = 86  # Set the maximum target temperature
        self._attr_target_temperature_low = 50  # Set the minimum target temperature
        self._attr_available = True  # Track availability
        self._enable_turn_on_off_backwards_compatibility = False

    @property
    def name(self):
        """Return the name of the heater."""
        return f"Envi Heater {self.external_id}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self.external_id

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return (ClimateEntityFeature.TARGET_TEMPERATURE |
                ClimateEntityFeature.TARGET_TEMPERATURE_RANGE |
                ClimateEntityFeature.TURN_ON |
                ClimateEntityFeature.TURN_OFF)
    
    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return self._target_temperature

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        return self._attr_hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return self._attr_hvac_modes

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._attr_temperature_unit

    @property
    def target_temperature_high(self):
        """Return the maximum target temperature."""
        return self._attr_target_temperature_high

    @property
    def target_temperature_low(self):
        """Return the minimum target temperature."""
        return self._attr_target_temperature_low

    @property
    def available(self):
        """Return True if entity is available."""
        return self._attr_available

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            await self.api_turn_on()
            self._attr_hvac_mode = HVACMode.HEAT
        elif hvac_mode == HVACMode.OFF:
            await self.api_turn_off()
            self._attr_hvac_mode = HVACMode.OFF
        else:
            _LOGGER.warning(f"Unsupported HVAC mode: {hvac_mode}")

    async def api_turn_on(self):
        url = f"https://app-apis.enviliving.com/apis/v1/device/update-temperature/{self.external_id}"
        headers = {'Authorization': f'Bearer {self.token}'}
        payload = {'state': 1}
        async with self.hass.helpers.aiohttp_client.async_get_clientsession().patch(url, headers=headers, json=payload) as response:
            response.raise_for_status()
        self._attr_hvac_mode = HVACMode.HEAT

    async def api_turn_off(self):
        url = f"https://app-apis.enviliving.com/apis/v1/device/update-temperature/{self.external_id}"
        headers = {'Authorization': f'Bearer {self.token}'}
        payload = {'state': 0}
        async with self.hass.helpers.aiohttp_client.async_get_clientsession().patch(url, headers=headers, json=payload) as response:
            response.raise_for_status()
        self._attr_hvac_mode = HVACMode.OFF

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        try:
            await self.api_set_temperature(temperature)
        except Exception as e:
            _LOGGER.error(f"An unexpected error occurred while setting the temperature: {e}")

    async def api_set_temperature(self, temperature):
        url = f"https://app-apis.enviliving.com/apis/v1/device/update-temperature/{self.external_id}"
        headers = {'Authorization': f'Bearer {self.token}'}
        payload = {'temperature': temperature}
        async with self.hass.helpers.aiohttp_client.async_get_clientsession().patch(url, headers=headers, json=payload) as response:
            response.raise_for_status()
        self._target_temperature = temperature

    async def async_update(self):
        """Fetch new state data for the heater."""
        await self.api_get_current_state()

    async def api_get_current_state(self):
        """Retrieve current state from the API."""
        url = f"https://app-apis.enviliving.com/apis/v1/device/{self.external_id}"
        headers = {'Authorization': f"Bearer {self.token}"}
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url, headers=headers) as response:
                if response.status in (401, 403):  # Unauthorized or invalid
                    new_token = await self.api.authenticate()
                    if new_token:
                        # Update the token in hass.data
                        self.hass.data[DOMAIN][self.entry.entry_id]['token'] = new_token
                        self.token = new_token
                        headers['Authorization'] = f"Bearer {new_token}"

                        # Update the config entry with the new token
                        self.hass.config_entries.async_update_entry(self.entry, data={**self.entry.data, 'token': new_token})

                        # Retry the request with the new token
                        async with session.get(url, headers=headers) as response:
                            response.raise_for_status()
                            resp_json = await response.json()
                    else:
                        _LOGGER.error("Failed to refresh token")
                        self._attr_available = False
                        return
                else:
                    response.raise_for_status()
                    resp_json = await response.json()

                if resp_json['status'] == 'success':
                    data = resp_json['data']
                    self._current_temperature = data['ambient_temperature'] # This is the temp of the room
                    self._target_temperature = data['current_temperature']  # This is the temp the device will get to
                    self._attr_hvac_mode = HVACMode.HEAT if data['state'] == 1 else HVACMode.OFF
                    self._attr_available = data['status'] == 1
                else:
                    _LOGGER.error(f"Failed to retrieve current state: {resp_json}")
                    self._attr_available = False
        except Exception as e:
            _LOGGER.error(f"An unexpected error occurred while fetching the state: {e}")
            self._attr_available = False
