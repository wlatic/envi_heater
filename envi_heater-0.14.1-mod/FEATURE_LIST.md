# Feature List - Envi Heater Integration

## Overview

This document details all features currently implemented in the Envi Heater Home Assistant custom component.

## Core Features

### 1. Climate Entity (Temperature Control)
**File**: `climate.py`

#### Temperature Control
- ✅ Set target temperature (with unit conversion)
- ✅ Read current ambient temperature
- ✅ Automatic temperature unit conversion (Celsius ↔ Fahrenheit)
- ✅ Respects device's native temperature unit

#### Power Control
- ✅ Turn heater ON
- ✅ Turn heater OFF
- ✅ Read current power state

#### Mode Control
- ✅ Set HVAC mode (Heat/Auto)
- ✅ Read current mode
- ✅ Mode mapping (numeric → human-readable)

#### Device Information
- ✅ Device name (from API)
- ✅ Firmware version
- ✅ Model number
- ✅ Serial number
- ✅ Location (in device name)

#### Extra State Attributes
- ✅ Signal strength (%)
- ✅ WiFi SSID
- ✅ Location name
- ✅ Firmware version
- ✅ Model number
- ✅ Serial number
- ✅ Mode (human-readable and numeric)
- ✅ Temperature unit (C/F)
- ✅ Schedule active status
- ✅ Schedule name
- ✅ Schedule temperature
- ✅ Freeze protection status (corrected for API inversion)
- ✅ Child lock status (corrected for API inversion)
- ✅ Hold status
- ✅ Geofence active status
- ✅ Last update timestamp

#### UI Features
- ✅ Dynamic icons (changes based on on/off state)
- ✅ Proper device registry entry
- ✅ Configuration URL to Envi app
- ✅ Device name includes location

### 2. Binary Sensors (Monitoring)
**File**: `binary_sensor.py`

#### Available Binary Sensors
1. **Freeze Protection** (`binary_sensor.envi_heater_{device_id}_freeze_protect`)
   - Device class: `SAFETY`
   - Icon: `mdi:snowflake-alert`
   - Category: Diagnostic
   - Status: Monitors freeze protection setting (read-only)

2. **Child Lock** (`binary_sensor.envi_heater_{device_id}_child_lock`)
   - Device class: `LOCK`
   - Category: Diagnostic
   - Status: Monitors child lock setting (read-only)

3. **Schedule Active** (`binary_sensor.envi_heater_{device_id}_schedule_active`)
   - Device class: `RUNNING`
   - Icon: `mdi:calendar-clock`
   - Category: Diagnostic
   - Status: Shows if schedule is currently active

4. **Hold** (`binary_sensor.envi_heater_{device_id}_hold`)
   - Device class: `RUNNING`
   - Icon: `mdi:pause-circle`
   - Category: Diagnostic
   - Status: Monitors hold status (read-only)

5. **Online** (`binary_sensor.envi_heater_{device_id}_online`)
   - Device class: `CONNECTIVITY`
   - Category: Diagnostic
   - Status: Shows device connectivity status

#### Features
- ✅ All sensors use coordinator (efficient updates)
- ✅ Proper device classes for UI
- ✅ Entity categories for organization
- ✅ Correct handling of API value inversion
- ✅ Automatic updates every 30 seconds

### 3. Sensors (Information Display)
**File**: `sensor.py`

#### Available Sensors
1. **Signal Strength** (`sensor.envi_heater_{device_id}_signal_strength`)
   - Unit: Percentage (%)
   - State class: Measurement
   - Icon: Dynamic (4 levels based on strength)
   - Category: Diagnostic
   - Range: 0-100%

2. **Firmware Version** (`sensor.envi_heater_{device_id}_firmware_version`)
   - Icon: `mdi:chip`
   - Category: Diagnostic
   - Shows device firmware version

3. **Mode** (`sensor.envi_heater_{device_id}_mode`)
   - Icon: `mdi:thermostat`
   - Category: Diagnostic
   - Shows human-readable mode (Heat/Auto/etc.)
   - Extra attribute: Raw mode number

4. **Schedule Name** (`sensor.envi_heater_{device_id}_schedule_name`)
   - Icon: `mdi:calendar-clock`
   - Category: Diagnostic
   - Shows active schedule name or "None"

5. **Schedule Temperature** (`sensor.envi_heater_{device_id}_schedule_temperature`)
   - Unit: °C or °F (respects device unit)
   - State class: Measurement
   - Device class: Temperature
   - Icon: `mdi:thermometer`
   - Category: Diagnostic
   - Shows scheduled temperature in device's native unit

6. **WiFi Network** (`sensor.envi_heater_{device_id}_wifi_ssid`)
   - Icon: `mdi:wifi`
   - Category: Diagnostic
   - Shows WiFi network name device is connected to

7. **Location** (`sensor.envi_heater_{device_id}_location`)
   - Icon: `mdi:map-marker`
   - Category: Diagnostic
   - Shows device location name

8. **Model** (`sensor.envi_heater_{device_id}_model`)
   - Icon: `mdi:tag`
   - Category: Diagnostic
   - Shows device model number

9. **Serial Number** (`sensor.envi_heater_{device_id}_serial`)
   - Icon: `mdi:barcode`
   - Category: Diagnostic
   - Shows device serial number

10. **Last Update** (`sensor.envi_heater_{device_id}_last_update`)
    - Device class: Timestamp
    - Icon: `mdi:clock-outline`
    - Category: Diagnostic
    - Shows last device update timestamp

#### Features
- ✅ All sensors use coordinator (efficient updates)
- ✅ Proper device classes and state classes
- ✅ Entity categories for organization
- ✅ Dynamic icons where applicable
- ✅ Temperature unit handling
- ✅ Automatic updates every 30 seconds

### 4. Data Update Coordinator
**File**: `coordinator.py`

#### Features
- ✅ Centralized data fetching
- ✅ Single API call per update cycle (instead of N calls)
- ✅ 30-second update interval
- ✅ Parallel device fetching using `asyncio.gather`
- ✅ Graceful error handling per device
- ✅ Device data caching
- ✅ Manual device refresh support
- ✅ Automatic retry on authentication errors
- ✅ Preserves previous data on transient errors

#### Benefits
- **Performance**: ~66% reduction in API calls (3 devices)
- **Efficiency**: Coordinated updates instead of individual polling
- **Reliability**: Better error handling at coordinator level
- **Consistency**: All entities see same data snapshot
- **Scalability**: Easy to add more entities without performance impact

### 5. API Client
**File**: `api.py`

#### Authentication
- ✅ JWT token-based authentication
- ✅ Automatic token refresh
- ✅ Token expiry detection
- ✅ Retry on authentication failures

#### Device Management
- ✅ Fetch all device IDs
- ✅ Get device state/information
- ✅ Update device temperature
- ✅ Update device state (on/off)
- ✅ Update device mode

#### Schedule Management
- ✅ List all schedules
- ✅ Get specific schedule
- ✅ Create schedule
- ✅ Update schedule
- ✅ Delete schedule

#### Device Settings (Read-Only)
- ✅ Get night light settings
- ✅ Get pilot light settings
- ✅ Get display settings
- ✅ Get freeze protection status (read-only)
- ✅ Get child lock status (read-only)
- ✅ Get notification settings (read-only)
- ✅ Get hold status (read-only)

#### Error Handling
- ✅ Custom exception types:
  - `EnviApiError` - General API errors
  - `EnviAuthenticationError` - Authentication failures
  - `EnviDeviceError` - Device-specific errors
- ✅ Detailed error messages with API error codes
- ✅ Network error handling
- ✅ JSON parsing error handling
- ✅ Automatic retry on auth failures

#### Utilities
- ✅ Temperature conversion (Celsius ↔ Fahrenheit)
- ✅ Complete device information retrieval

### 6. Services
**File**: `services.py`

#### Available Services

1. **`envi_heater.refresh_all`**
   - Refreshes all devices for all config entries
   - Uses coordinator for efficiency
   - Returns refresh count and error count

2. **`envi_heater.get_status`**
   - Gets detailed device status
   - Parameters: `entity_id` (required)
   - Returns: Comprehensive device information
   - Logs detailed status to Home Assistant logs

3. **`envi_heater.set_schedule`**
   - Sets or updates schedule for a device
   - Parameters:
     - `entity_id` (required)
     - `schedule` (required):
       - `enabled` (required)
       - `times` (optional): List of schedule times

4. **`envi_heater.test_connection`**
   - Tests API connection
   - Returns: Results dictionary per config entry
   - Logs connection test results

5. **`envi_heater.set_freeze_protect`** (Read-Only)
   - ⚠️ Raises error - Setting is read-only through API
   - Parameters: `entity_id`, `enabled`

6. **`envi_heater.set_child_lock`** (Read-Only)
   - ⚠️ Raises error - Setting is read-only through API
   - Parameters: `entity_id`, `enabled`

7. **`envi_heater.set_hold`** (Read-Only)
   - ⚠️ Raises error - Setting is read-only through API
   - Parameters: `entity_id`, `enabled`

#### Service Features
- ✅ Proper schema validation
- ✅ Entity ID extraction from unique_id
- ✅ Error handling and logging
- ✅ Support for multiple config entries
- ✅ Coordinator-based refresh where applicable

### 7. Configuration Flow
**File**: `config_flow.py`

#### Features
- ✅ Username/password authentication
- ✅ Connection testing during setup
- ✅ Unique ID based on username
- ✅ Prevents duplicate entries
- ✅ Error handling for invalid credentials
- ✅ Error handling for connection issues

## Entity Count Per Device

- **1 Climate entity** (temperature, state, mode control)
- **5 Binary sensors** (freeze protect, child lock, schedule active, hold, online)
- **10 Sensors** (signal strength, firmware, mode, schedule name/temp, WiFi SSID, location, model, serial, last update)
- **Total: 16 entities per device**

## API Limitations

### Read-Only Settings
The following settings **cannot** be changed through the API:
- Freeze Protection
- Child Lock
- Notifications
- Hold
- Permanent Hold

These settings can only be changed through the Envi mobile app. Binary sensors are available for monitoring these settings.

### Controllable Settings
The following settings **can** be changed through the API:
- ✅ Temperature
- ✅ State (On/Off)
- ✅ Mode (Heat/Auto)

## UI Improvements

### Icons
- ✅ Dynamic icons based on state (climate entity)
- ✅ Dynamic icons based on signal strength (4 levels)
- ✅ Appropriate icons for all entities
- ✅ Device class-based icons for binary sensors

### Organization
- ✅ Entity categories (diagnostic entities properly categorized)
- ✅ Device classes for proper UI representation
- ✅ State classes for sensors
- ✅ Device registry with location in name
- ✅ Configuration URL to Envi app

### User Experience
- ✅ Clean device view (diagnostic entities can be hidden/shown)
- ✅ Proper entity names with device name prefix
- ✅ Comprehensive device information in attributes
- ✅ Helpful error messages

## Performance Features

### Efficiency
- ✅ Single API call per update cycle (coordinator)
- ✅ Parallel device fetching
- ✅ Efficient data caching
- ✅ Coordinated updates

### Reliability
- ✅ Graceful error handling
- ✅ Previous data preservation on errors
- ✅ Per-device error handling
- ✅ Automatic token refresh
- ✅ Retry logic for authentication

### Scalability
- ✅ Easy to add more entities
- ✅ Coordinator pattern supports growth
- ✅ Efficient resource usage

## Testing & Development Tools

### Test Scripts Created
1. **`test_api_scanner.py`** - Comprehensive API endpoint discovery
2. **`test_all_controls.py`** - Tests all device controls
3. **`test_settings_endpoint.py`** - Tests settings endpoints
4. **`discover_endpoints.py`** - Advanced endpoint discovery (50+ patterns)

### Documentation
- ✅ `API_ENHANCEMENTS.md` - API capabilities
- ✅ `API_LIMITATIONS.md` - API limitations
- ✅ `BINARY_SENSORS.md` - Binary sensor documentation
- ✅ `SENSORS.md` - Sensor documentation
- ✅ `COORDINATOR_IMPLEMENTATION.md` - Coordinator details
- ✅ `INTEGRATION_SUMMARY.md` - Integration overview
- ✅ `COMPLETE_FEATURES.md` - Feature summary
- ✅ `TROUBLESHOOTING.md` - Troubleshooting guide
- ✅ `NEXT_STEPS.md` - Roadmap
- ✅ `IMPROVEMENTS.md` - Potential improvements
- ✅ `UI_IMPROVEMENTS_SUMMARY.md` - UI improvements summary

## Version Information

- **Manifest Version**: 1.0.0
- **Integration Domain**: `envi_heater`
- **Integration Name**: Envi Smart Heater
- **IoT Class**: Cloud Polling
- **Requirements**: `aiohttp>=3.8.4`

## Summary

The integration provides:
- ✅ Full temperature and power control
- ✅ Comprehensive device monitoring (16 entities per device)
- ✅ Efficient data updates (coordinator pattern)
- ✅ Professional UI organization
- ✅ Robust error handling
- ✅ Extensive documentation
- ✅ Development and testing tools

**Total Features**: 50+ implemented features across climate control, monitoring, API integration, and UI improvements.


