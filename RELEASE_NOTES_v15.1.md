# Release v15.1 - Code Quality Improvements

## Improvements

### Constants Organization
- Moved `SCAN_INTERVAL` to `const.py` for easier configuration
- Moved temperature limits (`MIN_TEMPERATURE`, `MAX_TEMPERATURE`) to constants
- Added `BASE_URL` and `ENDPOINTS` dictionary for API endpoints
- All magic numbers now centralized for maintainability

### Service Helper Functions
- Created `_get_device_id_from_entity()` helper function
  - Uses entity registry API (preferred method)
  - Falls back to parsing if registry unavailable
- Created `_get_client_from_domain()` helper function
  - Centralized client lookup logic
  - Reduces code duplication across services

### Error Handling Improvements
- Wrapped exceptions in `HomeAssistantError` for user-friendly messages
- Better error messages in climate control methods
- Improved service error handling with clear user feedback

### Code Quality
- Standardized device_id handling throughout codebase
- Added complete type hints to all service functions
- Improved code organization and maintainability
- Reduced code duplication significantly

## Technical Details
- All API endpoints now use constants from `ENDPOINTS` dictionary
- Device ID extraction uses proper Home Assistant entity registry API
- Consistent error handling patterns across all modules

## No Breaking Changes
This is a maintenance release with no breaking changes. All existing functionality remains the same.

