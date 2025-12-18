# Release v15.3.2 - Remove services.yaml for HA 2025.12

## 🐛 Bug Fix

### Fixed Service Discovery Error
- **Fixed**: `Failed to load services.yaml for integration: smart_envi`
- **Root Cause**: In Home Assistant 2025.12, `services.yaml` is optional for programmatic service registration, but Home Assistant was trying to load it and failing
- **Solution**: Removed `services.yaml` file since services are registered programmatically in `services.py`
- **Impact**: Eliminates error message in logs

## 🔧 Technical Details

In Home Assistant 2025.12, when services are registered programmatically (as they are in this integration), the `services.yaml` file is optional. However, if the file exists, Home Assistant attempts to load it, which was causing the error.

Since all services are properly registered in `services.py` using `hass.services.async_register()`, the `services.yaml` file is not needed and removing it resolves the error.

## ✅ What This Fixes

**Before:**
```
Failed to load services.yaml for integration: smart_envi
NoneType: None
```

**After:**
- No more service discovery errors
- Services continue to work as before (registered programmatically)
- Cleaner logs

## 🔄 Migration Notes

- **No Breaking Changes**: This is a bug fix only
- **No Migration Required**: Existing configurations continue to work
- **Services Unaffected**: All services continue to work exactly as before

## 📊 Changes

- **Files Changed**: 1 file removed (`services.yaml`)
- **Impact**: Fixes service discovery error in Home Assistant 2025.12

## 🎯 Testing

After updating to v15.3.2:
1. Restart Home Assistant or reload the Smart Envi integration
2. Verify no "Failed to load services.yaml" errors in logs
3. Confirm all services still work correctly
4. Test services in Home Assistant Developer Tools → Services

## 📝 Technical Notes

- Services are registered programmatically in `services.py` using `async_setup_services()`
- This is the correct approach for Home Assistant 2025.12
- The `services.yaml` file was causing unnecessary errors

## 🙏 Credits

- **Current Maintainer**: [@rendershome](https://github.com/rendershome)

---

**Full Changelog**: 
- Commit `26d4fbe`: Remove services.yaml - not needed for programmatic service registration in HA 2025.12

