# Release v15.0 - Major Feature Release

## Major Features

### DataUpdateCoordinator
- Centralized data management with parallel device updates
- Efficient updates every 30 seconds for all devices
- Graceful error handling with cached data fallback

### Sensor Platform
Added 10 diagnostic sensors per device:
- Signal Strength
- Firmware Version
- Mode
- Schedule Name
- Schedule Temperature
- WiFi Network (SSID)
- Location
- Model
- Serial Number
- Last Update

### Binary Sensor Platform
Added 5 binary sensors per device:
- Freeze Protection
- Child Lock
- Schedule Active
- Hold
- Online Status

### Enhanced API Client
- Better error handling with detailed messages
- Automatic token refresh with JWT parsing
- Temperature conversion utilities (Celsius/Fahrenheit)
- Schedule management (CRUD operations)

### Improved Climate Entities
- Proper device registry integration with location support
- Temperature unit conversion support
- Enhanced device information
- Extra state attributes with comprehensive device data

## Technical Improvements
- Renamed from `envi_heater` to `smart_envi`
- Production-ready logging and monitoring
- Better error recovery and graceful degradation

## Breaking Changes
- Domain changed from `envi_heater` to `smart_envi`
- Service names changed (e.g., `envi_heater.refresh_all` → `smart_envi.refresh_all`)
- Entity IDs changed (e.g., `climate.envi_heater_12345` → `climate.smart_envi_12345`)

## Migration Notes
- Remove old integration and re-add to get new entities
- Update any automations/scripts using old service names
- Update entity IDs in your configuration

