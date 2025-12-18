# Envi Smart Heater - Home Assistant Integration

> **⚠️ DISCLAIMER**: This is an **UNOFFICIAL** integration. This integration is not created, maintained, or endorsed by EHEAT, Inc. or Envi. It uses the Envi API in an unofficial capacity. Use at your own risk.

Custom component for Home Assistant to interact with [Envi eHeat Smart Heaters](https://www.eheat.com/).

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

![Envi eHeat integration preview](example.png)

## Features

- **Full Climate Control**: Temperature control (50°F - 86°F) and on/off functionality
- **Comprehensive Sensors**: 10 diagnostic sensors per device
- **Status Monitoring**: 5 binary sensors for device status
- **Efficient Updates**: DataUpdateCoordinator with parallel device updates
- **Temperature Conversion**: Automatic Celsius/Fahrenheit support
- **Custom Services**: Advanced scheduling and status monitoring

## Installation

### Via HACS

1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the three dots menu → Custom repositories
4. Add this repository URL
5. Search for "Envi Smart Heater" and install
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/smart_envi` folder to your `custom_components` directory
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Envi Smart Heater"
4. Enter your Envi account credentials
5. The integration will automatically discover your heaters

## What Gets Created

For each heater:
- **1 Climate Entity**: Temperature control and on/off
- **10 Sensor Entities**: Signal strength, firmware, mode, schedule info, WiFi, location, model, serial, last update
- **5 Binary Sensors**: Freeze protect, child lock, schedule active, hold, online

## Requirements

- Home Assistant 2023.1 or later
- Envi account with active heaters
- Internet connection

## Documentation

See the [full documentation](custom_components/smart_envi/README.md) for detailed usage, services, and troubleshooting.

## ⚠️ Disclaimer

This is an **UNOFFICIAL** integration. This integration is not created, maintained, or endorsed by EHEAT, Inc. or Envi. It uses the Envi API in an unofficial capacity. Use at your own risk.

## Credits

- **Original Author**: [@wlatic](https://github.com/wlatic) - Initial Envi Heater integration
- **Manufacturer**: [EHEAT, Inc.](https://www.eheat.com/) - Envi Smart Heaters

## Support

For issues, feature requests, or questions, please open an issue on GitHub.
