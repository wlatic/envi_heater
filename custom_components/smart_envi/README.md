# Envi Smart Heater Integration

A comprehensive Home Assistant integration for Envi Smart Heaters with enhanced reliability, error handling, and advanced features.

## 🚀 What's New in v15.0

### Major Improvements
- **DataUpdateCoordinator**: Centralized data management with parallel device updates
- **Sensor Platform**: 10 diagnostic sensors per device (signal strength, firmware, mode, schedule info, etc.)
- **Binary Sensor Platform**: 5 binary sensors per device (freeze protect, child lock, schedule active, hold, online)
- **Enhanced API Client**: Better error handling, token management, and retry logic
- **Temperature Conversion**: Automatic Celsius/Fahrenheit conversion support
- **Improved Entity Management**: Proper device information and availability tracking
- **Custom Services**: Advanced functionality for scheduling and status monitoring
- **Better Error Recovery**: Graceful degradation and detailed error reporting
- **Production Ready**: Comprehensive logging and monitoring

### Key Features

#### 🔧 Enhanced API Client
- **Smart Token Management**: Automatic token refresh with expiration tracking
- **Retry Logic**: Automatic retry on authentication failures
- **Error Classification**: Specific error types for better debugging
- **Connection Resilience**: Handles network issues gracefully
- **Temperature Conversion**: Built-in C/F conversion utilities
- **Schedule Management**: Full CRUD operations for heating schedules

#### 🏠 Improved Climate Entities
- **Device Information**: Proper device registry integration with location support
- **Availability Tracking**: Real-time connection status via coordinator
- **Better State Management**: Accurate temperature and mode tracking
- **Temperature Unit Support**: Automatic conversion between Celsius and Fahrenheit
- **Extra State Attributes**: Signal strength, WiFi SSID, location, firmware version, schedule info, and more
- **Error Handling**: Specific error messages for different failure types
- **Coordinator-Based**: Uses DataUpdateCoordinator for efficient updates

#### 📊 Sensor Entities
Each heater automatically creates 10 diagnostic sensors:
- **Signal Strength**: WiFi signal strength percentage
- **Firmware Version**: Device firmware version
- **Mode**: Current operating mode (Heat, Auto, etc.)
- **Schedule Name**: Name of active schedule
- **Schedule Temperature**: Temperature set by active schedule
- **WiFi Network**: Connected WiFi SSID
- **Location**: Device location name
- **Model**: Device model number
- **Serial Number**: Device serial number
- **Last Update**: Timestamp of last device update

#### 🔘 Binary Sensor Entities
Each heater automatically creates 5 binary sensors:
- **Freeze Protection**: Freeze protection status (on/off)
- **Child Lock**: Child lock status (locked/unlocked)
- **Schedule Active**: Whether a schedule is currently active
- **Hold**: Whether device is in hold mode
- **Online**: Device connectivity status

#### 🛠️ Custom Services
- `smart_envi.refresh_all`: Refresh all heaters via coordinator
- `smart_envi.set_schedule`: Set heating schedules
- `smart_envi.get_status`: Get detailed device status
- `smart_envi.test_connection`: Test API connection
- `smart_envi.set_freeze_protect`: Enable/disable freeze protection (read-only via API)
- `smart_envi.set_child_lock`: Enable/disable child lock (read-only via API)
- `smart_envi.set_hold`: Set temporary hold (read-only via API)

## 📋 Installation

1. Copy the `smart_envi` folder to your `custom_components` directory
2. Restart Home Assistant
3. Add the integration via the UI

## 🔧 Configuration

The integration uses the standard Home Assistant config flow:

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Envi Smart Heater"
4. Enter your Envi account credentials
5. The integration will automatically discover your heaters and create all entities

## 🎯 Usage

### Basic Climate Control
The integration creates climate entities for each Envi heater:
- **Temperature Control**: Set target temperature (50°F - 86°F)
- **On/Off Control**: Turn heaters on/off
- **Current Temperature**: Real-time ambient temperature reading
- **Temperature Unit**: Automatically handles Celsius/Fahrenheit conversion

### Sensor Entities
All sensors are automatically created and update every 30 seconds:
- View device diagnostics in the sensor entities
- Use sensors in automations and dashboards
- Sensors are categorized as diagnostic entities

### Binary Sensors
Monitor device status with binary sensors:
- Use in automations to detect freeze protection, child lock, etc.
- Online sensor helps track device connectivity
- Schedule active sensor shows when schedules are running

### Custom Services

#### Refresh All Heaters
```yaml
service: smart_envi.refresh_all
```

#### Set Heater Schedule
```yaml
service: smart_envi.set_schedule
data:
  entity_id: climate.smart_envi_12345
  schedule:
    enabled: true
    times:
      - time: "08:00:00"
        temperature: 72
        enabled: true
      - time: "18:00:00"
        temperature: 68
        enabled: true
```

#### Get Heater Status
```yaml
service: smart_envi.get_status
data:
  entity_id: climate.smart_envi_12345
```

#### Test Connection
```yaml
service: smart_envi.test_connection
```

**Note**: Some settings (freeze protect, child lock, hold) cannot be changed via the API and will return an error. These must be changed through the Envi mobile app.

## 🔍 Troubleshooting

### Common Issues

#### "Authentication failed"
- Check your Envi account credentials
- Ensure your account has active heaters
- Try re-authenticating via the integration settings

#### "No devices found"
- Verify you have Envi heaters in your account
- Check the Envi app to ensure heaters are online
- Restart the integration

#### "Device unavailable"
- Check your internet connection
- Verify the Envi API is accessible
- Check the Home Assistant logs for specific errors
- Check the "Online" binary sensor for connectivity status

#### "Services not working"
- Ensure services are properly registered (check logs)
- Verify entity IDs are correct
- Some services may be read-only (see service descriptions)

### Debug Logging

Enable debug logging to see detailed information:

```yaml
logger:
  logs:
    custom_components.smart_envi: debug
```

## 🏗️ Architecture

### Components

- **API Client** (`api.py`): Handles all Envi API communication with token management
- **Coordinator** (`coordinator.py`): DataUpdateCoordinator for centralized device updates
- **Climate Platform** (`climate.py`): Home Assistant climate entities using coordinator
- **Sensor Platform** (`sensor.py`): Diagnostic sensor entities
- **Binary Sensor Platform** (`binary_sensor.py`): Status binary sensor entities
- **Config Flow** (`config_flow.py`): Setup and configuration
- **Services** (`services.py`): Custom Home Assistant services

### Update Mechanism

The integration uses a DataUpdateCoordinator that:
- Updates all devices in parallel every 30 seconds
- Fetches device list on each update to handle new devices
- Maintains cached data for offline devices
- Provides efficient updates to all entity types

### Error Handling

The integration includes comprehensive error handling:

- **EnviApiError**: General API errors with detailed messages
- **EnviAuthenticationError**: Authentication failures with automatic retry
- **EnviDeviceError**: Device-specific errors
- **UpdateFailed**: Coordinator update failures with graceful degradation

### Token Management

- Automatic token refresh before expiration (5 minute buffer)
- JWT token parsing for accurate expiration tracking
- Concurrent request protection with asyncio locks
- Graceful fallback for authentication failures

## 🔄 Updates

The integration automatically updates device states every 30 seconds via the coordinator:
- All devices update in parallel for efficiency
- Immediate refresh after user actions (temperature changes, on/off)
- Coordinator handles errors gracefully, keeping previous data when possible

## 📊 Monitoring

Monitor your integration health through:
- Home Assistant device registry (shows all entities per device)
- Integration status in Settings → Devices & Services
- Online binary sensor for device connectivity
- Debug logs for detailed operation information
- Sensor entities for device diagnostics

## 🤝 Contributing

This integration is designed to be robust and user-friendly. If you encounter issues:

1. Check the troubleshooting section
2. Enable debug logging
3. Review the Home Assistant logs
4. Check sensor and binary sensor values for diagnostics
5. Report issues with detailed logs

## 📝 Changelog

### v15.0
- **DataUpdateCoordinator**: Implemented centralized data management
- **Sensor Platform**: Added 10 diagnostic sensors per device
- **Binary Sensor Platform**: Added 5 binary sensors per device
- **Temperature Conversion**: Automatic C/F conversion support
- **Enhanced Services**: Improved service implementations with coordinator support
- **Better Error Handling**: Detailed error messages and graceful degradation
- **Performance**: Parallel device updates for better efficiency
- **Device Info**: Enhanced device information with location support

### v1.0.0
- Complete rewrite with enhanced reliability
- Added custom services
- Improved error handling
- Better device integration
- Production-ready logging
- JWT auth added

### v0.10.0
- Initial release
- Basic climate control
- Simple API integration
