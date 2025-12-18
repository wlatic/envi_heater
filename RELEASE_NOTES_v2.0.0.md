# Release v2.0.0 - First Official Release

## 🎉 Overview

**v2.0.0** is the **first official release** of the Smart Envi integration for Home Assistant. This release consolidates all development work from the pre-release phase (v15.*) into a stable, production-ready integration.

### Pre-Release Phase

All versions **v15.0 through v15.3.9** were pre-releases used for testing and development. These versions have been consolidated into this official v2.0.0 release. Users upgrading from any v15.* version should follow the migration guide below.

## 📜 History

### Original Fork (v0.10.0, v1.0.0)
- **Original Author**: [@wlatic](https://github.com/wlatic)
- Initial Envi Heater integration with basic climate control
- Simple API integration and JWT authentication

### Pre-Release Phase (v15.*)
- **Current Maintainer**: [@rendershome](https://github.com/rendershome)
- Complete rewrite with enhanced reliability
- Major feature additions and improvements
- Extensive testing and refinement
- All v15.* releases were pre-releases for testing

### Official Release (v2.0.0)
- **Production Ready**: Stable, tested, and documented
- **Consolidated Features**: All improvements from pre-release phase
- **Full History**: Complete feature set documented below

## ✨ Complete Feature List

### 🏠 Climate Control
- **Full Temperature Control**: Set target temperature (50°F - 86°F)
- **On/Off Control**: Turn heaters on/off via Home Assistant
- **Current Temperature**: Real-time ambient temperature reading
- **Temperature Unit Support**: Automatic Celsius/Fahrenheit conversion
- **Mode Management**: Heat, Auto, and other operating modes
- **Device Information**: Proper device registry integration with location support
- **Extra State Attributes**: Signal strength, WiFi SSID, location, firmware version, schedule info, and more

### 📊 Sensor Platform (10 Sensors per Device)
Each heater automatically creates diagnostic sensors:
- **Signal Strength**: WiFi signal strength percentage
- **Firmware Version**: Device firmware version
- **Mode**: Current operating mode (Heat, Auto, etc.)
- **Schedule Name**: Name of active schedule
- **Schedule Temperature**: Temperature set by active schedule
- **WiFi Network**: Connected WiFi SSID
- **Location**: Device location name
- **Model**: Device model number
- **Serial Number**: Device serial number
- **Last Update**: Timestamp of last device update (timezone-aware)

### 🔘 Binary Sensor Platform (5 Sensors per Device)
Each heater automatically creates status sensors:
- **Freeze Protection**: Freeze protection status (on/off)
- **Child Lock**: Child lock status (locked/unlocked)
- **Schedule Active**: Whether a schedule is currently active
- **Hold**: Whether device is in hold mode
- **Online**: Device connectivity status

### 🔧 Enhanced API Client
- **Smart Token Management**: Automatic token refresh with JWT expiration tracking
- **Retry Logic with Exponential Backoff**: Automatic retry for transient network errors (up to 3 attempts)
  - Exponential backoff delays: 1s, 2s, 4s (max 30s)
  - Retries for server errors (500, 502, 503, 504)
  - Better handling of network timeouts and connection errors
- **Rate Limiting Protection**: 
  - Detects HTTP 429 (Too Many Requests) responses
  - Respects `Retry-After` header from API
  - Automatic backoff when rate limited
  - Prevents API bans during high activity
- **Data Validation**: 
  - Validates API response structure before processing
  - Enhanced validation for device list responses
  - Better handling of invalid or malformed data
  - Prevents crashes from unexpected API changes
- **Temperature Conversion**: Built-in C/F conversion utilities
- **Schedule Management**: Full CRUD operations for heating schedules
- **Error Classification**: Specific error types (EnviApiError, EnviAuthenticationError, EnviDeviceError)
- **Connection Resilience**: Handles network issues gracefully

### 📅 Schedule Management
- **UI Form**: Interactive schedule editor in Home Assistant options flow
- **Service Support**: `smart_envi.get_schedule` and `smart_envi.set_schedule` services
- **Full CRUD**: Create, read, update, and delete schedules
- **Multiple Time Entries**: Support for complex schedules with multiple time slots
- **Schedule Examples**: Built-in help text with sample schedules
- **Temperature Range**: 50-86°F validation

### 🔄 DataUpdateCoordinator
- **Centralized Data Management**: Single source of truth for all device data
- **Parallel Updates**: All devices update simultaneously for efficiency
- **Configurable Polling**: Adjustable scan interval (10-300 seconds, default 30s)
- **Configurable Timeout**: Adjustable API timeout (5-60 seconds, default 15s)
- **Graceful Error Handling**: Cached data fallback when devices temporarily fail
- **Per-Device Error Recovery**: Individual device failures don't affect others
- **Enhanced Logging**: Detailed update cycle logging with success/failure counts

### 🛠️ Custom Services
- `smart_envi.refresh_all`: Refresh all heaters via coordinator
- `smart_envi.get_schedule`: Get current schedule for a heater
- `smart_envi.set_schedule`: Create or update heating schedules
- `smart_envi.get_status`: Get detailed device status
- `smart_envi.test_connection`: Test API connection
- `smart_envi.set_freeze_protect`: Attempt to set freeze protection (read-only via API)
- `smart_envi.set_child_lock`: Attempt to set child lock (read-only via API)
- `smart_envi.set_hold`: Attempt to set temporary hold (read-only via API)

### 🎨 User Interface
- **Config Flow**: Standard Home Assistant setup wizard
- **Options Flow**: 
  - Integration settings (polling interval, API timeout)
  - Schedule editor with UI form
  - Device selection dropdown
- **Help Text**: Comprehensive inline help via `strings.json`
  - Polling interval guidance
  - API timeout troubleshooting
  - Schedule format examples
  - Sample schedules (Morning/Evening, Work Day, Weekend, All Day)

### 🛡️ Error Handling & Reliability
- **Comprehensive Error Handling**: 
  - Specific error types for different failure scenarios
  - User-friendly error messages
  - Graceful degradation
- **Better Error Recovery**: 
  - Coordinator error handling with cached data fallback
  - Per-device error recovery
  - Enhanced logging with full context
- **Production-Ready Logging**: 
  - Debug logging support
  - Detailed operation information
  - Error tracking and diagnostics

### 📝 Documentation
- **Comprehensive README**: Full documentation with examples
- **Troubleshooting Guide**: Common issues and solutions
- **Service Documentation**: Detailed service usage examples
- **Architecture Documentation**: Component overview and design decisions
- **Migration Guide**: Step-by-step upgrade instructions

### ⚠️ Legal & Attribution
- **Official Disclaimers**: Prominent warnings about unofficial status
- **Manufacturer Attribution**: Proper attribution to EHEAT, Inc. (https://www.eheat.com/)
- **Product Name**: Consistent "Smart Envi" naming throughout
- **Credits**: Original author and current maintainer properly credited

## 🔄 Breaking Changes

### Domain Change
- **Old Domain**: `envi_heater`
- **New Domain**: `smart_envi`
- **Impact**: 
  - Service names changed (e.g., `envi_heater.refresh_all` → `smart_envi.refresh_all`)
  - Entity IDs changed (e.g., `climate.envi_heater_12345` → `climate.smart_envi_12345`)
  - Configuration entry domain changed

### Migration Required
If upgrading from the original `envi_heater` integration or any v15.* pre-release:

1. **Remove Old Integration**:
   - Go to Settings → Devices & Services
   - Find the old integration
   - Click the three dots menu → Delete
   - Confirm deletion

2. **Install New Integration**:
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "Envi Smart Heater" or "Smart Envi"
   - Enter your Envi account credentials
   - Complete setup

3. **Update Automations/Scripts**:
   - Update service names from `envi_heater.*` to `smart_envi.*`
   - Update entity IDs from `climate.envi_heater_*` to `climate.smart_envi_*`
   - Update sensor entity IDs similarly
   - Update binary sensor entity IDs similarly

4. **Verify Entities**:
   - Check that all entities are created correctly
   - Verify sensor and binary sensor entities appear
   - Test climate control functionality
   - Test custom services

## 📋 Installation

### HACS (Recommended)
1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the three dots menu → Custom repositories
4. Add repository URL: `https://github.com/rendershome/smart_envi`
5. Search for "Envi Smart Heater" and install
6. Restart Home Assistant

### Manual Installation
1. Download the latest release from GitHub
2. Copy the `custom_components/smart_envi` folder to your `custom_components` directory
3. Restart Home Assistant
4. Add the integration via Settings → Devices & Services → Add Integration

## 🎯 Usage

### Basic Climate Control
Control your heaters through the climate entities:
- Set target temperature (50°F - 86°F)
- Turn heaters on/off
- View current ambient temperature
- Monitor device status

### Schedule Management
- **Via UI**: Use the options flow to edit schedules with the interactive form
- **Via Services**: Use `smart_envi.get_schedule` and `smart_envi.set_schedule` services
- **Sample Schedules**: See help text in the options flow for examples

### Sensor Monitoring
- View device diagnostics in sensor entities
- Use sensors in automations and dashboards
- Monitor connectivity via Online binary sensor
- Track schedule status via Schedule Active binary sensor

## 🔍 Troubleshooting

### Common Issues

#### "Authentication failed"
- Check your Envi account credentials
- Ensure your account has active heaters
- Try re-authenticating via the integration settings

#### "No devices found"
- Verify you have Envi heaters in your account
- Check the Envi app to ensure heaters are online
- Restart the integration

#### "Device unavailable"
- Check your internet connection
- Verify the Envi API is accessible
- Check the Home Assistant logs for specific errors
- Check the "Online" binary sensor for connectivity status

### Debug Logging
Enable debug logging to see detailed information:

```yaml
logger:
  logs:
    custom_components.smart_envi: debug
```

## 📊 Technical Details

### Requirements
- Home Assistant 2023.1 or later
- Python 3.9 or later
- aiohttp >= 3.8.4
- Envi account with active heaters
- Internet connection

### Architecture
- **API Client** (`api.py`): Handles all Envi API communication with token management
- **Coordinator** (`coordinator.py`): DataUpdateCoordinator for centralized device updates
- **Climate Platform** (`climate.py`): Home Assistant climate entities using coordinator
- **Sensor Platform** (`sensor.py`): Diagnostic sensor entities
- **Binary Sensor Platform** (`binary_sensor.py`): Status binary sensor entities
- **Config Flow** (`config_flow.py`): Setup and configuration with options flow
- **Services** (`services.py`): Custom Home Assistant services
- **Strings** (`strings.json`): UI text and help descriptions

### Update Mechanism
- Updates all devices in parallel every 30 seconds (configurable)
- Fetches device list on each update to handle new devices
- Maintains cached data for offline devices
- Provides efficient updates to all entity types
- Immediate refresh after user actions

### Error Handling
- **EnviApiError**: General API errors with detailed messages
- **EnviAuthenticationError**: Authentication failures with automatic retry
- **EnviDeviceError**: Device-specific errors
- **UpdateFailed**: Coordinator update failures with graceful degradation

### Token Management
- Automatic token refresh before expiration (5 minute buffer)
- JWT token parsing for accurate expiration tracking
- Concurrent request protection with asyncio locks
- Graceful fallback for authentication failures

## ⚠️ Disclaimer

This is an **UNOFFICIAL** integration. This integration is:
- **NOT** created, maintained, or endorsed by EHEAT, Inc. or Envi
- **NOT** an official Home Assistant integration
- Uses the Envi API in an **unofficial capacity**
- Provided "as-is" without warranty
- May stop working if EHEAT changes their API

Use at your own risk. The developers are not responsible for any issues that may arise from using this integration.

## 🙏 Credits

- **Original Author**: [@wlatic](https://github.com/wlatic) - Initial Envi Heater integration (v0.10.0, v1.0.0)
- **Current Maintainer**: [@rendershome](https://github.com/rendershome) - Enhanced and maintained for the Home Assistant community
- **Manufacturer**: [EHEAT, Inc.](https://www.eheat.com/) - Envi Smart Heaters
- Uses the Envi API for device communication (unofficial use)

## 📝 Changelog Summary

### v2.0.0 (Official Release)
- **First Official Release**: Consolidates all pre-release development
- **Complete Feature Set**: All features from v15.* pre-releases
- **Production Ready**: Stable, tested, and documented
- **Full History**: Complete development history documented

### Pre-Release Phase (v15.0 - v15.3.9)
All v15.* versions were pre-releases for testing and development. Key milestones:

- **v15.0**: DataUpdateCoordinator, sensor platform, binary sensor platform
- **v15.1**: Additional improvements
- **v15.2**: Retry logic, rate limiting, data validation, official disclaimers
- **v15.2.1 - v15.2.4**: Bug fixes and improvements
- **v15.3.0 - v15.3.6**: Additional features and fixes
- **v15.3.7**: Enhanced options flow help text
- **v15.3.8**: Fixed options flow description parameter error
- **v15.3.9**: Proper help text display via strings.json

### Original Fork (v0.10.0, v1.0.0)
- Initial release with basic climate control
- Simple API integration
- JWT authentication

---

**Full Changelog**: See git history for complete development timeline.

