# Release v15.2.2 - Options Flow Fix for Home Assistant 2025.12

## Bug Fixes

### Fixed Options Flow Initialization
- **Fixed**: Options flow initialization error for Home Assistant 2025.12
- **Issue**: OptionsFlowHandler was not properly initialized, causing 500 errors
- **Solution**: Restored proper `__init__` method with config_entry parameter
- **Impact**: Users can now access configuration options via gear icon

### Improved Error Handling
- Added comprehensive try/except blocks around options flow
- Better error messages and logging
- Graceful fallback if options flow fails
- Added debug logging for troubleshooting

### Code Quality
- Fixed indentation issues
- Improved validation logic for scan_interval and api_timeout
- Better type conversion handling

## What This Fixes

Previously, clicking the gear icon (⚙️) next to the Envi Smart Heater integration would show:
```
Config flow could not be loaded: 500 Internal Server Error
Server got itself in trouble
```

This release fixes that error, allowing users to:
- ✅ Access the configure menu via gear icon
- ✅ Change scan interval (poll time): 10-300 seconds
- ✅ Change API timeout: 5-60 seconds
- ✅ Save configuration changes successfully

## Compatibility

- **Tested with**: Home Assistant 2025.12
- **Backward compatible**: Works with earlier HA versions

## No Breaking Changes
This is a bug fix release. All existing functionality remains the same.

## Migration Notes
- No migration required
- Existing configurations continue to work
- Users can now access previously unavailable configuration options

