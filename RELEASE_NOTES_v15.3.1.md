# Release v15.3.1 - Timestamp Parsing Fix & Service Discovery

## 🐛 Critical Bug Fixes

### Fixed Timestamp Sensor Error
- **Fixed**: `AttributeError: 'str' object has no attribute 'tzinfo'` in `last_update` sensor
- **Root Cause**: The `last_update` sensor with `SensorDeviceClass.TIMESTAMP` was returning a string instead of a datetime object
- **Impact**: Sensor was causing errors in Home Assistant logs and not displaying correctly

### Fixed Service Discovery Error
- **Fixed**: `Failed to load services.yaml for integration: smart_envi`
- **Root Cause**: Home Assistant was looking for a `services.yaml` file for service discovery
- **Impact**: Error message in logs (non-critical, services still worked)
- **Solution**: Added `services.yaml` file with service metadata for proper discovery

## 🔧 Technical Details

### Problem
The `EnviLastUpdateSensor` was using `SensorDeviceClass.TIMESTAMP` which requires a datetime object, but the API was returning timestamps in various formats (including space-separated format like "2025-12-18 01:07:44") that weren't being parsed correctly.

### Solution
- **Enhanced Timestamp Parsing**: Added support for multiple timestamp formats:
  - ISO format with "Z" (e.g., "2025-12-18T01:07:44Z")
  - ISO format with timezone (e.g., "2025-12-18T01:07:44+00:00")
  - Space-separated format (e.g., "2025-12-18 01:07:44") - **This was the failing format**
  - ISO format with "T" separator
  - Formats with microseconds
  
- **Type Safety**: Added explicit type checking to ensure datetime objects are always returned (never strings)
- **Error Handling**: Improved error handling with better logging for debugging
- **Timezone Handling**: Ensures all datetime objects are timezone-aware (defaults to UTC)

## ✅ What This Fixes

**Before:**
```
ValueError: Invalid datetime: sensor.bedroom_last_update has timestamp device class 
but provides state 2025-12-18 01:07:44:<class 'str'> resulting in 
''str' object has no attribute 'tzinfo''
```

**After:**
- Timestamp is correctly parsed into a datetime object
- Sensor displays correctly in Home Assistant
- No more errors in logs

## 🔄 Migration Notes

- **No Breaking Changes**: This is a bug fix only
- **No Migration Required**: Existing configurations continue to work
- **Automatic Fix**: After updating, the sensor will automatically start working correctly

## 📊 Changes

- **Files Changed**: 2 files (`sensor.py`, `services.yaml`)
- **Lines Changed**: +109 insertions, -7 deletions
- **Impact**: Fixes critical error affecting all users with `last_update` sensors and service discovery warning

## 🎯 Testing

After updating to v15.3.1:
1. Restart Home Assistant or reload the Smart Envi integration
2. Check that `last_update` sensors display correctly
3. Verify no errors in logs related to timestamp parsing
4. Confirm sensor shows proper datetime values in Home Assistant UI
5. Verify no "Failed to load services.yaml" errors in logs
6. Confirm all services are discoverable in Home Assistant Developer Tools → Services

## 📝 Technical Notes

The fix ensures that:
- All timestamp formats from the Envi API are properly handled
- Datetime objects are always returned (never strings) for TIMESTAMP device class
- Proper timezone handling (UTC default)
- Graceful fallback to `None` if parsing fails (instead of crashing)

## 🙏 Credits

- **Current Maintainer**: [@rendershome](https://github.com/rendershome)

---

**Full Changelog**: 
- Commit `ddce0f5`: Fix timestamp parsing for last_update sensor
- Commit `cb90c1a`: Add services.yaml file for service discovery

