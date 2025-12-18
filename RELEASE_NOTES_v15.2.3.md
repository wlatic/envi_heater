# Release v15.2.3 - Additional Options Flow Fixes

## Bug Fixes

### Options Flow Improvements
- Added `super().__init__()` call to OptionsFlowHandler initialization
- Added error handling to options flow creation
- Improved error logging for debugging
- Better exception handling throughout options flow

### Compatibility
- Tested with Home Assistant 2025.12
- Improved initialization pattern for OptionsFlow

## Technical Details

This release includes additional fixes to address options flow initialization issues:
- Proper parent class initialization with `super().__init__()`
- Error handling wrapper around options flow creation
- Enhanced logging for troubleshooting

## Troubleshooting

If you still experience issues accessing the configure menu:

1. **Check Home Assistant Logs**: Settings → System → Logs
   - Look for errors mentioning `smart_envi` or `config_flow`
   - Enable debug logging: Add to `configuration.yaml`:
     ```yaml
     logger:
       logs:
         custom_components.smart_envi: debug
     ```

2. **Verify Version**: Ensure you're on v15.2.3
   - Check `manifest.json` in `custom_components/smart_envi/`

3. **Clear Cache**: 
   - Restart Home Assistant
   - Clear browser cache (Ctrl+F5)

## No Breaking Changes
This is a bug fix release. All existing functionality remains the same.

