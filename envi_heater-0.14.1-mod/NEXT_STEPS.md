# Next Steps Roadmap

## 🎯 Priority 1: Testing & Validation (Do First!)

### 1.1 Test in Home Assistant
- [ ] Install integration in Home Assistant
- [ ] Verify climate entities appear correctly
- [ ] Test temperature setting (both directions)
- [ ] Test on/off functionality
- [ ] Verify device info (firmware, model, serial)
- [ ] Check temperature unit conversion works

### 1.2 Test All Services
- [ ] `envi_heater.refresh_all` - Verify it refreshes all devices
- [ ] `envi_heater.get_status` - Check returned data structure
- [ ] `envi_heater.set_freeze_protect` - Test enable/disable
- [ ] `envi_heater.set_child_lock` - Test enable/disable
- [ ] `envi_heater.set_hold` - Test enable/disable
- [ ] `envi_heater.set_schedule` - **Needs API payload verification**
- [ ] `envi_heater.test_connection` - Verify connection testing

### 1.3 Verify Schedule Payload Format
The schedule service needs the correct API payload structure. Use the API scanner to:
- [ ] Check actual schedule data structure from `schedule/list`
- [ ] Test `schedule/add` endpoint with different payloads
- [ ] Document the correct payload format
- [ ] Update `set_schedule` service implementation

## 🚀 Priority 2: Performance & Architecture (Important)

### 2.1 Implement DataUpdateCoordinator
**Current Issue**: Each entity polls individually (inefficient)

**Solution**: Create a coordinator for centralized updates
- [ ] Create `coordinator.py` file
- [ ] Implement `EnviDataUpdateCoordinator` class
- [ ] Update climate entities to use coordinator
- [ ] Set appropriate update interval (30 seconds recommended)
- [ ] Handle errors gracefully at coordinator level

**Benefits**:
- Single API call per update cycle (instead of N calls)
- Better error handling
- More efficient resource usage
- Easier to add more entities later

### 2.2 Improve Polling Strategy
- [ ] Add configurable update interval
- [ ] Implement exponential backoff on errors
- [ ] Add option to disable polling (webhook support if available)

## 🔧 Priority 3: Additional Services (Nice to Have)

### 3.1 Night Light Services
API methods exist but no services yet:
- [ ] `envi_heater.set_night_light` - Control night light
  - Parameters: `entity_id`, `brightness`, `color` (RGB), `auto`, `on`
- [ ] `envi_heater.get_night_light` - Get night light settings

### 3.2 Pilot Light Services
- [ ] `envi_heater.set_pilot_light` - Control pilot light
  - Parameters: `entity_id`, `brightness`, `always_on`, `auto_dim`, `auto_dim_time`
- [ ] `envi_heater.get_pilot_light` - Get pilot light settings

### 3.3 Display Settings Services
- [ ] `envi_heater.set_display` - Control display settings
  - Parameters: `entity_id`, `brightness`, `timeout`, `auto`
- [ ] `envi_heater.get_display` - Get display settings

### 3.4 Mode Control Service
- [ ] `envi_heater.set_mode` - Set device mode
  - Parameters: `entity_id`, `mode` (1=heat, 3=auto, etc.)

## 📊 Priority 4: Additional Entities (Enhancement)

### 4.1 Binary Sensors
Create binary sensors for device states:
- [ ] `binary_sensor.envi_heater_freeze_protect` - Freeze protection status
- [ ] `binary_sensor.envi_heater_child_lock` - Child lock status
- [ ] `binary_sensor.envi_heater_schedule_active` - Schedule active status
- [ ] `binary_sensor.envi_heater_hold` - Hold status
- [ ] `binary_sensor.envi_heater_online` - Device online status

### 4.2 Sensors
Create sensors for device information:
- [ ] `sensor.envi_heater_signal_strength` - WiFi signal strength (%)
- [ ] `sensor.envi_heater_firmware_version` - Firmware version
- [ ] `sensor.envi_heater_mode` - Current mode (heat/auto/etc.)
- [ ] `sensor.envi_heater_schedule_name` - Active schedule name
- [ ] `sensor.envi_heater_schedule_temperature` - Scheduled temperature

### 4.3 Switches
**Note**: Switches for read-only settings have been removed. These settings (freeze protect, child lock, notifications, hold) cannot be controlled through the API and can only be changed via the Envi mobile app. Binary sensors are available for monitoring these settings.

### 4.4 Number Entities
For settings that need numeric input:
- [ ] `number.envi_heater_night_light_brightness` - Night light brightness (0-100)
- [ ] `number.envi_heater_pilot_light_brightness` - Pilot light brightness (0-100)
- [ ] `number.envi_heater_display_brightness` - Display brightness (0-100)

## 🎨 Priority 5: User Experience (Polish)

### 5.1 Better Entity Names
- [ ] Use device name + location (e.g., "Bedroom - Basement")
- [ ] Add friendly names from API
- [ ] Support custom names via config

### 5.2 Device Attributes
Expose more data as entity attributes:
- [ ] Signal strength
- [ ] WiFi SSID
- [ ] Last update time
- [ ] Schedule information
- [ ] Mode information
- [ ] Settings status

### 5.3 Icons & UI
- [ ] Add appropriate icons for different states
- [ ] Add device class for better UI representation
- [ ] Consider custom card/lovelace card

## 📝 Priority 6: Documentation (Important for Sharing)

### 6.1 Update README
- [ ] Document all new services
- [ ] Add usage examples
- [ ] Add troubleshooting section
- [ ] Document temperature unit handling
- [ ] Add screenshots

### 6.2 API Documentation
- [ ] Document discovered endpoints
- [ ] Document payload formats
- [ ] Add API response examples
- [ ] Document error codes

### 6.3 User Guide
- [ ] Step-by-step installation guide
- [ ] Configuration examples
- [ ] Automation examples
- [ ] Common use cases

## 🐛 Priority 7: Bug Fixes & Edge Cases

### 7.1 Error Handling
- [ ] Handle network timeouts gracefully
- [ ] Handle API rate limiting
- [ ] Handle invalid device IDs
- [ ] Handle missing device data

### 7.2 Edge Cases
- [ ] Handle devices with no schedules
- [ ] Handle devices with no location
- [ ] Handle temperature unit changes
- [ ] Handle multiple accounts

### 7.3 Validation
- [ ] Validate temperature ranges
- [ ] Validate service parameters
- [ ] Validate device IDs
- [ ] Add input validation

## 🔮 Priority 8: Future Enhancements (Research Needed)

### 8.1 Geofence Support
- [ ] Discover geofence endpoints
- [ ] Implement geofence management
- [ ] Add geofence entities

### 8.2 Device Groups
- [ ] Support device grouping
- [ ] Group control services
- [ ] Group scheduling

### 8.3 Statistics & History
- [ ] Energy usage tracking (if available)
- [ ] Temperature history
- [ ] Usage statistics

### 8.4 Advanced Features
- [ ] Webhook support (if API supports it)
- [ ] Push notifications
- [ ] Device sharing
- [ ] Firmware update notifications

## 📋 Quick Start Checklist

If you want to get started quickly, focus on these:

1. **Test the integration** (Priority 1.1)
2. **Implement DataUpdateCoordinator** (Priority 2.1) - Biggest performance win
3. **Add binary sensors** (Priority 4.1) - Easy wins, high value
4. **Fix schedule service** (Priority 1.3) - Complete the feature
5. **Update documentation** (Priority 6.1) - Important for sharing

## 🎯 Recommended Order

1. **Week 1**: Testing & Validation + DataUpdateCoordinator
2. **Week 2**: Binary Sensors + Additional Services
3. **Week 3**: More Sensors/Switches + Documentation
4. **Week 4**: Polish & Edge Cases

## 💡 Quick Wins (Easy & High Value)

These can be done quickly and add significant value:

1. **Binary Sensors** - 30 minutes each, high visibility
2. **Signal Strength Sensor** - 15 minutes, useful info
3. **Mode Sensor** - 15 minutes, helpful for debugging
4. **Better Entity Attributes** - 30 minutes, more data visible
5. **Update README** - 1 hour, helps users

## 🤝 Contributing

If you're sharing this with the original developer or community:

1. Test everything thoroughly
2. Document all changes
3. Add code comments
4. Follow Home Assistant coding standards
5. Create pull request with clear description

---

**Current Status**: Integration is functional with enhanced API capabilities. Ready for testing and further enhancement.

