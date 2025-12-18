"""Config flow for Smart Envi."""
from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnviApiClient, EnviAuthenticationError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Default values
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_API_TIMEOUT = 15  # seconds
MIN_SCAN_INTERVAL = 10  # seconds - minimum to avoid API overload
MAX_SCAN_INTERVAL = 300  # seconds - 5 minutes max
MIN_API_TIMEOUT = 5  # seconds
MAX_API_TIMEOUT = 60  # seconds


class EnviHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Smart Envi."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input["username"]
            password = user_input["password"]

            await self.async_set_unique_id(username.lower())
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = EnviApiClient(session, username, password)

            try:
                await client.authenticate()
                return self.async_create_entry(
                    title=f"Smart Envi ({username})",
                    data=user_input,
                )
            except EnviAuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> EnviHeaterOptionsFlowHandler:
        """Get the options flow for this handler."""
        return EnviHeaterOptionsFlowHandler()


class EnviHeaterOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Smart Envi."""

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the options."""
        _LOGGER.debug("Options flow init step called, user_input: %s", user_input)
        errors: dict[str, str] = {}
        
        try:
            if user_input is not None:
                # Validate scan interval
                scan_interval = user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL)
                try:
                    scan_interval = int(scan_interval)
                except (ValueError, TypeError):
                    errors["scan_interval"] = "Scan interval must be a number"
                
                if not errors.get("scan_interval"):
                    if scan_interval < MIN_SCAN_INTERVAL or scan_interval > MAX_SCAN_INTERVAL:
                        errors["scan_interval"] = f"Scan interval must be between {MIN_SCAN_INTERVAL} and {MAX_SCAN_INTERVAL} seconds"
                
                # Validate API timeout
                api_timeout = user_input.get("api_timeout", DEFAULT_API_TIMEOUT)
                try:
                    api_timeout = int(api_timeout)
                except (ValueError, TypeError):
                    errors["api_timeout"] = "API timeout must be a number"
                
                if not errors.get("api_timeout"):
                    if api_timeout < MIN_API_TIMEOUT or api_timeout > MAX_API_TIMEOUT:
                        errors["api_timeout"] = f"API timeout must be between {MIN_API_TIMEOUT} and {MAX_API_TIMEOUT} seconds"

                if not errors:
                    # Store options
                    return self.async_create_entry(
                        title="",
                        data={
                            "scan_interval": scan_interval,
                            "api_timeout": api_timeout,
                        },
                    )

            # Get current values from config entry
            options = self.config_entry.options or {}
            current_scan_interval = options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
            current_api_timeout = options.get("api_timeout", DEFAULT_API_TIMEOUT)
            
            # Ensure values are integers
            try:
                current_scan_interval = int(current_scan_interval)
            except (ValueError, TypeError):
                current_scan_interval = DEFAULT_SCAN_INTERVAL
            
            try:
                current_api_timeout = int(current_api_timeout)
            except (ValueError, TypeError):
                current_api_timeout = DEFAULT_API_TIMEOUT

            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            "scan_interval",
                            default=current_scan_interval,
                        ): vol.All(
                            vol.Coerce(int),
                            vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                        ),
                        vol.Required(
                            "api_timeout",
                            default=current_api_timeout,
                        ): vol.All(
                            vol.Coerce(int),
                            vol.Range(min=MIN_API_TIMEOUT, max=MAX_API_TIMEOUT),
                        ),
                    }
                ),
                errors=errors,
                description_placeholders={
                    "min_scan": str(MIN_SCAN_INTERVAL),
                    "max_scan": str(MAX_SCAN_INTERVAL),
                    "min_timeout": str(MIN_API_TIMEOUT),
                    "max_timeout": str(MAX_API_TIMEOUT),
                },
            )
        except Exception as err:
            _LOGGER.exception("Error in options flow: %s", err)
            errors["base"] = "unknown"
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema({
                    vol.Required("scan_interval", default=DEFAULT_SCAN_INTERVAL): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Required("api_timeout", default=DEFAULT_API_TIMEOUT): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_API_TIMEOUT, max=MAX_API_TIMEOUT),
                    ),
                }),
                errors=errors,
            )
