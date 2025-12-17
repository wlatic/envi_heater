# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-12-XX

### Added
- **DataUpdateCoordinator**: Implemented centralized data polling for efficient API usage (~66% reduction in API calls)
- **16 entities per device**:
  - 1 Climate entity (temperature, power, mode control)
  - 5 Binary sensors (freeze protect, child lock, schedule active, hold, online)
  - 10 Sensors (signal strength, firmware, mode, schedule info, WiFi, location, model, serial, etc.)
- **Enhanced API Client**: 20+ new methods for comprehensive device control and monitoring
- **7 Custom Services**: Advanced control capabilities via Home Assistant services
- **Automatic Temperature Unit Conversion**: Supports both Celsius and Fahrenheit
- **Dynamic Icons**: Icons change based on device state
- **Entity Categories**: Proper organization of diagnostic entities
- **Device Registry Enhancements**: Location information, configuration URLs, firmware/model/serial numbers
- **Comprehensive Error Handling**: Custom exceptions, retry logic, graceful degradation
- **Parallel Device Fetching**: All devices fetched simultaneously for better performance
- **Extensive Documentation**: Feature lists, troubleshooting guides, API limitations

### Changed
- **Climate Entity**: Now uses CoordinatorEntity for efficient updates
- **API Polling**: Switched from individual device polling to coordinator-based updates
- **Temperature Handling**: Respects device's native temperature unit (Celsius/Fahrenheit)
- **UI Organization**: Diagnostic entities properly categorized

### Fixed
- **Temperature Unit Display**: Schedule temperature sensor now correctly displays device's native unit
- **Binary Sensor Logic**: Fixed inverted logic for freeze protect and child lock sensors
- **API Endpoint Errors**: Corrected 404 errors by using proper endpoints
- **Service Registration**: Fixed services not being registered on startup

### Removed
- **Switch Platform**: Removed switches for read-only settings (freeze protect, child lock, notifications, hold) as these cannot be controlled via API

### Known Limitations
- Some settings (freeze protect, child lock, notifications, hold) are read-only via API and can only be changed through the Envi mobile app
- These settings are available as binary sensors for monitoring

## [0.14.1] - Original Version

### Features
- Basic climate entity
- Temperature and power control
- Config flow integration


