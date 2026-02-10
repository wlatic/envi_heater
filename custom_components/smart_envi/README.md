# Envi Smart Heater Integration

> **⚠️ DISCLAIMER**: This is an **UNOFFICIAL** integration. This integration is not created, maintained, or endorsed by EHEAT, Inc. or Envi. It uses the Envi API in an unofficial capacity. Use at your own risk.

A comprehensive Home Assistant integration for Envi Smart Heaters (manufactured by [EHEAT, Inc.](https://www.eheat.com/)) with enhanced reliability, error handling, and advanced features.

## 🚀 Features

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
- `smart_envi.get_schedule`: Get current schedule for a heater
- `smart_envi.set_schedule`: Create or update heating schedules
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

#### Get Heater Schedule
Retrieve the current schedule for a heater. This is useful to see the existing schedule before editing it.

```yaml
service: smart_envi.get_schedule
data:
  entity_id: climate.smart_envi_12345
```

**Response** (available in Developer Tools → Services → Call Service → Show response):
```yaml
schedule_id: 12345
device_id: "abc123"
enabled: true
name: "My Schedule"
temperature: 72
times:
  - time: "08:00:00"
    temperature: 72
    enabled: true
  - time: "18:00:00"
    temperature: 68
    enabled: true
```

#### Set Heater Schedule
Create or update a schedule for a heater. If the device already has a schedule, it will be updated. Otherwise, a new schedule will be created.

**To edit an existing schedule:**
1. First, use `smart_envi.get_schedule` to retrieve the current schedule
2. Modify the schedule data as needed
3. Use `smart_envi.set_schedule` to update it

```yaml
service: smart_envi.set_schedule
data:
  entity_id: climate.smart_envi_12345
  schedule:
    enabled: true
    name: "My Schedule"  # Optional
    times:
      - time: "08:00:00"
        temperature: 72
        enabled: true
      - time: "12:00:00"
        temperature: 70
        enabled: true
      - time: "18:00:00"
        temperature: 68
        enabled: true
      - time: "22:00:00"
        temperature: 65
        enabled: true
```

**Schedule Parameters:**
- `enabled`: `true` or `false` - Whether the schedule is active
- `name`: (optional) String - Name for the schedule
- `times`: (optional) List of time entries, each containing:
  - `time`: String in `HH:MM:SS` format (e.g., `"08:00:00"`)
  - `temperature`: Float between 50-86°F
  - `enabled`: `true` or `false` - Whether this time slot is active

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

- Automatic token refresh before expiration (5-minute buffer)
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

## ⚠️ Disclaimer

This is an **UNOFFICIAL** integration. This integration is:
- **NOT** created, maintained, or endorsed by EHEAT, Inc. or Envi
- **NOT** an official Home Assistant integration
- Uses the Envi API in an **unofficial capacity**
- Provided "as-is" without warranty
- May stop working if EHEAT changes their API

Use at your own risk. The developers are not responsible for any issues that may arise from using this integration.

## 🙏 Credits

- **Original Author**: [@wlatic](https://github.com/wlatic) - Initial Envi Heater integration
- **Current Maintainer**: [@rendershome](https://github.com/rendershome) - Enhanced with DataUpdateCoordinator, sensor platform, binary sensor platform, and improved error handling
- **Manufacturer**: [EHEAT, Inc.](https://www.eheat.com/) - Envi Smart Heaters

## 📝 Version History

### v2.0.0 (Current)
- **First Official Release**: Production-ready integration
- **Complete Feature Set**: All features consolidated from pre-release phase
- See [RELEASE_NOTES_v2.0.0.md](../../RELEASE_NOTES_v2.0.0.md) for full details

### Pre-Release Phase (v15.*)
All v15.* versions were pre-releases for testing and development. These have been consolidated into v2.0.0.

### Original Fork (v0.10.0, v1.0.0)
- **Original Author**: [@wlatic](https://github.com/wlatic)
- Initial Envi Heater integration with basic climate control
- Simple API integration and JWT authentication
