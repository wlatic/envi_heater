# Release v15.2.4 - Fix OptionsFlow Property Error

## Critical Bug Fix

### Fixed OptionsFlow Property Error
- **Fixed**: `AttributeError: property 'config_entry' of 'EnviHeaterOptionsFlowHandler' object has no setter`
- **Root Cause**: In Home Assistant 2025.12, `config_entry` is a read-only property set by the framework
- **Solution**: Removed `__init__` method and parameter - `config_entry` is automatically available via parent class
- **Impact**: Options flow now works correctly in Home Assistant 2025.12

## What Changed

**Before (causing error):**
```python
def __init__(self, config_entry: ConfigEntry) -> None:
    self.config_entry = config_entry  # ❌ Error: no setter
```

**After (fixed):**
```python
# No __init__ needed - config_entry is automatically available
# Access via self.config_entry (read-only property from parent)
```

## Compatibility

- **Fixed for**: Home Assistant 2025.12
- **Backward compatible**: Works with earlier HA versions
- **Tested**: Options flow now initializes correctly

## What This Fixes

The error:
```
AttributeError: property 'config_entry' of 'EnviHeaterOptionsFlowHandler' object has no setter
```

Is now resolved. Users can:
- ✅ Access configure menu via gear icon
- ✅ Change scan interval (poll time): 10-300 seconds  
- ✅ Change API timeout: 5-60 seconds
- ✅ Save configuration changes successfully

## No Breaking Changes
This is a bug fix release. All existing functionality remains the same.

## Migration Notes
- No migration required
- Update to v15.2.4 and restart Home Assistant
- Options flow will now work correctly

