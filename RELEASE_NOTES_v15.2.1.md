# Release v15.2.1 - Options Flow Bug Fix

## Bug Fixes

### Fixed Options Flow Configuration Error
- **Fixed**: 500 Internal Server Error when accessing configure menu via gear icon
- **Cause**: Missing `super().__init__()` call in OptionsFlowHandler initialization
- **Impact**: Users can now access configuration options to change poll time and API timeout

### Additional Improvements
- Added error handling for option value type conversion
- Ensures scan_interval and api_timeout are properly converted to integers
- Prevents type errors when loading existing configuration

## What This Fixes

Previously, clicking the gear icon (⚙️) next to the Envi Smart Heater integration would show:
```
Config flow could not be loaded: 500 Internal Server Error
Server got itself in trouble
```

This release fixes that error, allowing users to:
- Access the configure menu
- Change scan interval (poll time): 10-300 seconds
- Change API timeout: 5-60 seconds
- Save configuration changes

## No Breaking Changes
This is a bug fix release. All existing functionality remains the same.

## Migration Notes
- No migration required
- Existing configurations continue to work
- Users can now access previously unavailable configuration options

