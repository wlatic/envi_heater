# Release v15.3.8 - Fix Options Flow Description Parameter Error

## 🐛 Bug Fix

### Fixed Options Flow Error
- **Fixed**: `TypeError: FlowHandler.async_show_form() got an unexpected keyword argument 'description'`
- **Root Cause**: `async_show_form()` method doesn't accept a `description` parameter
- **Solution**: Removed form-level `description` parameters from `async_show_form()` calls
- **Impact**: Options flow now works correctly without errors

## What Changed

**Before (causing error):**
```python
return self.async_show_form(
    step_id="integration_options",
    data_schema=...,
    description="Configure how often..."  # ❌ Invalid parameter
)
```

**After (fixed):**
```python
return self.async_show_form(
    step_id="integration_options",
    data_schema=...,  # Field-level descriptions still work ✅
)
```

## Technical Details

- Field-level `description` parameters in `vol.Required()` and `vol.Optional()` work correctly
- Form-level `description` parameter is not supported by `async_show_form()`
- All help text remains available through field descriptions (click ? icons)

## What This Fixes

The error:
```
TypeError: FlowHandler.async_show_form() got an unexpected keyword argument 'description'
```

Is now resolved. Users can:
- ✅ Access integration options without errors
- ✅ Access schedule editor without errors
- ✅ See all help text via field descriptions (? icons)
- ✅ Configure settings successfully

## No Breaking Changes

This is a bug fix release. All existing functionality remains the same.

## Migration Notes

- No migration required
- Update to v15.3.8 and restart Home Assistant
- Options flow will now work correctly

---

**Full Changelog**: 
- Commit: Fix: Remove invalid description parameter from async_show_form

