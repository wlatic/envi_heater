# Envi Smart Heater - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A comprehensive Home Assistant custom component for Envi Smart Heaters with enhanced API capabilities, efficient data polling, and comprehensive device monitoring.

## Features

### 🎛️ Full Control
- **Temperature Control**: Set target temperature with automatic unit conversion (Celsius/Fahrenheit)
- **Power Control**: Turn heaters on/off
- **Mode Control**: Switch between Heat and Auto modes

### 📊 Comprehensive Monitoring
- **16 entities per device**:
  - 1 Climate entity (control)
  - 5 Binary sensors (freeze protect, child lock, schedule active, hold, online)
  - 10 Sensors (signal strength, firmware, mode, schedule info, WiFi, location, model, serial, etc.)

### ⚡ Performance Optimized
- **DataUpdateCoordinator**: Single API call per update cycle (instead of N calls)
- **Parallel fetching**: All devices fetched simultaneously
- **Efficient updates**: 30-second interval with coordinated refresh
- **~66% reduction** in API calls compared to individual polling

### 🎨 Professional UI
- Dynamic icons based on device state
- Proper entity categories (diagnostic entities organized)
- Device registry with location information
- Configuration URL to Envi app

### 🔧 Advanced Features
- **7 custom services** for advanced control
- **Automatic temperature unit conversion**
- **Comprehensive device information** in attributes
- **Robust error handling** with graceful degradation
- **Token management** with automatic refresh

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots (⋮) in the top right
4. Select "Custom repositories"
5. Add this repository URL
6. Select "Integration" as the category
7. Click "Add"
8. Find "Envi Smart Heater" in the HACS integrations list
9. Click "Install"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/envi_heater/` folder to your Home Assistant `custom_components/` directory
2. Restart Home Assistant
3. Add integration via Settings → Devices & Services → Add Integration → Envi Smart Heater
4. Enter your Envi account credentials

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Envi Smart Heater**
4. Enter your Envi account credentials:
   - **Username**: Your Envi account email
   - **Password**: Your Envi account password
5. Click **Submit**

The integration will automatically discover all your Envi heaters.

## Usage

### Climate Entity

The main climate entity provides:
- **Current Temperature**: Ambient temperature reading
- **Target Temperature**: Set your desired temperature
- **HVAC Mode**: Heat or Off
- **Power Control**: Turn heater on/off

### Binary Sensors

Monitor device states:
- **Freeze Protect**: Freeze protection status
- **Child Lock**: Child lock status
- **Schedule Active**: Whether schedule is currently active
- **Hold**: Temporary hold status
- **Online**: Device connectivity status

### Sensors

Additional device information:
- **Signal Strength**: WiFi signal strength (%)
- **Firmware Version**: Device firmware version
- **Mode**: Current operating mode
- **Schedule Name**: Active schedule name
- **Schedule Temperature**: Scheduled temperature
- **WiFi Network**: Connected WiFi SSID
- **Location**: Device location
- **Model**: Device model number
- **Serial Number**: Device serial number
- **Last Update**: Last data update timestamp

### Custom Services

Advanced control via services:

- `envi_heater.set_heater_schedule`: Set heater schedule
- `envi_heater.get_heater_status`: Get detailed device status
- `envi_heater.set_night_light_setting`: Control night light
- `envi_heater.set_pilot_light_setting`: Control pilot light
- `envi_heater.set_display_setting`: Control display settings
- `envi_heater.set_mode`: Set device mode
- `envi_heater.refresh_all_heaters`: Refresh all devices

See the [Feature List](FEATURE_LIST.md) for complete documentation.

## API Limitations

Some settings are **read-only** through the API and can only be changed via the Envi mobile app:
- Freeze Protection
- Child Lock  
- Notifications
- Hold

These settings are available as binary sensors for monitoring, but cannot be controlled through Home Assistant.

## Requirements

- Home Assistant 2023.x or later
- Envi account credentials
- `aiohttp>=3.8.4`

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## Documentation

- [Feature List](FEATURE_LIST.md) - Complete feature documentation
- [API Limitations](API_LIMITATIONS.md) - Known API constraints
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Debugging help
- [Integration Summary](INTEGRATION_SUMMARY.md) - Technical overview

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Credits

- Original integration by [wlatic](https://github.com/wlatic/envi_heater)
- Enhanced with comprehensive monitoring and efficient polling

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/wlatic/envi_heater/issues) page.

---

**Status**: Production Ready ✅

The integration is fully functional and ready for use. All core features are implemented and tested.
