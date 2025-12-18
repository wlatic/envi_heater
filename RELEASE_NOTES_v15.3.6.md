# Release v15.3.6 - Fix Menu Step Routing

## 🐛 Bug Fix

### Fixed Menu Step Routing Error
- **Fixed**: `UnknownStep: Handler EnviHeaterOptionsFlowHandler doesn't support step schedule`
- **Root Cause**: Menu selections in Home Assistant call step methods matching the menu option keys
- **Solution**: Added `async_step_integration` and `async_step_schedule` methods to properly route menu selections
- **Impact**: Options flow menu now works correctly

## What Changed

**Before (causing error):**
- Menu option "schedule" tried to call `async_step_schedule` which didn't exist
- Menu option "integration" tried to call `async_step_integration` which didn't exist

**After (fixed):**
- Added `async_step_schedule` method that routes to `async_step_select_device`
- Added `async_step_integration` method that routes to `async_step_integration_options`
- Menu selections now properly route to the correct steps

## Compatibility

- **Fixed for**: Home Assistant 2025.12
- **Backward compatible**: Works with earlier HA versions
- **Tested**: Menu routing now works correctly

## What This Fixes

The error:
```
UnknownStep: Handler EnviHeaterOptionsFlowHandler doesn't support step schedule
```

Is now resolved. Users can:
- ✅ Select "Edit Device Schedule" from the menu
- ✅ Select "Integration Settings" from the menu
- ✅ Navigate through the options flow without errors

## No Breaking Changes

This is a bug fix release. All existing functionality remains the same.

## Migration Notes

- No migration required
- Update to v15.3.6 and restart Home Assistant
- Menu routing will now work correctly

---

**Full Changelog**: 
- Commit: Fix menu step routing in options flow

