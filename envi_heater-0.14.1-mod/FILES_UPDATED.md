# Files Updated - Original Integration Files

## Original Files (Modified)

### 1. `custom_components/envi_heater/__init__.py`
**Status**: ✅ Modified
**Changes**:
- Added `EnviDataUpdateCoordinator` creation and storage
- Added `Platform.BINARY_SENSOR` and `Platform.SENSOR` to `PLATFORMS` list
- Removed `Platform.SWITCH` (settings are read-only)
- Integrated coordinator refresh before platform setup
- Added coordinator cleanup in `async_unload_entry`
- Ensured services setup only happens once per Home Assistant instance

### 2. `custom_components/envi_heater/api.py`
**Status**: ✅ Significantly Enhanced
**Changes**:
- Added comprehensive API methods for schedule management:
  - `get_schedule_list()`
  - `get_schedule()`
  - `create_schedule()`
  - `update_schedule()`
  - `delete_schedule()`
- Added device settings methods:
  - `get_night_light_setting()`
  - `set_night_light_setting()`
  - `get_pilot_light_setting()`
  - `set_pilot_light_setting()`
  - `get_display_setting()`
  - `set_display_setting()`
- Added device control methods (read-only - raise errors):
  - `set_freeze_protect()` - Raises error (read-only)
  - `set_child_lock()` - Raises error (read-only)
  - `set_notification_setting()` - Raises error (read-only)
  - `set_hold()` - Raises error (read-only)
  - `set_permanent_hold()` - Raises error (read-only)
- Enhanced error handling:
  - Better 400 Bad Request handling
  - More descriptive error messages
  - Improved token refresh logic
- Added utility methods:
  - `convert_temperature()` - Temperature unit conversion
  - `get_device_full_info()` - Complete device information
- Improved `get_device_state()` to return full device data

### 3. `custom_components/envi_heater/climate.py`
**Status**: ✅ Significantly Enhanced
**Changes**:
- Converted to use `CoordinatorEntity` instead of individual polling
- Removed `_attr_should_poll = False` (coordinator handles updates)
- Added dynamic icons based on state:
  - `mdi:radiator` when ON
  - `mdi:radiator-off` when OFF
- Enhanced `device_info`:
  - Includes firmware version
  - Includes model number
  - Includes serial number
  - Includes location in device name
  - Added `configuration_url` to Envi app
- Enhanced `extra_state_attributes` with comprehensive device information:
  - Signal strength, WiFi SSID, location
  - Schedule information (name, temperature, active status)
  - Device settings (freeze protect, child lock, hold)
  - Mode information (human-readable and raw)
  - Device metadata (firmware, model, serial)
- Improved temperature unit handling:
  - Automatic detection of device temperature unit
  - Conversion between Celsius and Fahrenheit
  - Proper handling when setting temperatures
- Better error handling and logging
- Immediate refresh after state changes

### 4. `custom_components/envi_heater/services.py`
**Status**: ✅ Enhanced
**Changes**:
- Enhanced `refresh_all_heaters()`:
  - Now uses coordinator for efficient refresh
  - Better error reporting with counts
  - Handles multiple config entries
- Enhanced `get_heater_status()`:
  - Returns comprehensive device information
  - Better logging format
  - Returns data for automation use
- Enhanced `test_connection()`:
  - Returns results dictionary
  - Better error handling
  - Supports multiple config entries
- Added new services (read-only - raise errors):
  - `set_freeze_protect` - Raises error (read-only)
  - `set_child_lock` - Raises error (read-only)
  - `set_hold` - Raises error (read-only)
- Improved service schemas and validation
- Better error messages

### 5. `custom_components/envi_heater/config_flow.py`
**Status**: ✅ Unchanged (No modifications needed)

### 6. `custom_components/envi_heater/const.py`
**Status**: ✅ Unchanged (No modifications needed)

### 7. `custom_components/envi_heater/manifest.json`
**Status**: ✅ Unchanged (Version may need update)

### 8. `custom_components/envi_heater/README.md`
**Status**: ✅ Unchanged (Original documentation)

## New Files Created

### 1. `custom_components/envi_heater/coordinator.py`
**Status**: ✅ New File
**Purpose**: Centralized data update coordinator for efficient API polling
**Features**:
- Single API call per update cycle (instead of N calls)
- 30-second update interval
- Parallel device fetching using `asyncio.gather`
- Graceful error handling per device
- Manual device refresh support
- Device data caching

### 2. `custom_components/envi_heater/binary_sensor.py`
**Status**: ✅ New File
**Purpose**: Binary sensors for device state monitoring
**Entities**:
- Freeze Protection status
- Child Lock status
- Schedule Active status
- Hold status
- Online status

### 3. `custom_components/envi_heater/sensor.py`
**Status**: ✅ New File
**Purpose**: Sensors for device information display
**Entities**:
- Signal Strength (with dynamic icons)
- Firmware Version
- Mode (human-readable)
- Schedule Name
- Schedule Temperature (respects device unit)
- WiFi SSID
- Location
- Model
- Serial Number
- Last Update

## Files Removed

### 1. `custom_components/envi_heater/switch.py`
**Status**: ❌ Removed
**Reason**: Settings (freeze protect, child lock, notifications, hold) are read-only through the API and cannot be controlled. Binary sensors remain for monitoring.

## Summary

- **Original Files Modified**: 4 files (`__init__.py`, `api.py`, `climate.py`, `services.py`)
- **New Files Created**: 3 files (`coordinator.py`, `binary_sensor.py`, `sensor.py`)
- **Files Removed**: 1 file (`switch.py`)
- **Files Unchanged**: 4 files (`config_flow.py`, `const.py`, `manifest.json`, `README.md`)


