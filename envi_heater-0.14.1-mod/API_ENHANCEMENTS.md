# Envi API Client Enhancements

## Overview
The API client has been significantly enhanced with new capabilities discovered through API scanning.

## New Features

### 1. Schedule Management
Full CRUD operations for schedules:

- `get_schedule_list()` - Get all schedules
- `get_schedule(schedule_id)` - Get specific schedule
- `create_schedule(schedule_data)` - Create new schedule
- `update_schedule(schedule_id, schedule_data)` - Update existing schedule
- `delete_schedule(schedule_id)` - Delete schedule

**Example:**
```python
# Get all schedules
schedules = await client.get_schedule_list()

# Create a new schedule
schedule_data = {
    "name": "Morning Warm",
    "device_id": 12345,  # Replace with your device ID
    "temperature": 21,
    "time": "07:00",
    "days": ["monday", "tuesday", "wednesday"]
}
await client.create_schedule(schedule_data)
```

### 2. Device Settings Management

#### Night Light Settings
- `get_night_light_setting(device_id)` - Get current settings
- `set_night_light_setting(device_id, brightness, color, auto, on)` - Update settings

#### Pilot Light Settings
- `get_pilot_light_setting(device_id)` - Get current settings
- `set_pilot_light_setting(device_id, brightness, always_on, auto_dim, auto_dim_time)` - Update settings

#### Display Settings
- `get_display_setting(device_id)` - Get current settings
- `set_display_setting(device_id, display_brightness, timeout)` - Update settings

**Example:**
```python
# Set night light to 50% brightness
await client.set_night_light_setting(
    device_id="12345",  # Replace with your device ID
    brightness=50,
    auto=False,
    on=True
)
```

### 3. Device Control Features

#### Basic Control
- `set_temperature(device_id, temperature)` - Set target temperature
- `set_state(device_id, state)` - Turn device on/off (1=on, 0=off)
- `set_mode(device_id, mode)` - Set device mode (1=heat, 3=auto)

#### Advanced Features
- `set_child_lock(device_id, enabled)` - Enable/disable child lock
- `set_freeze_protect(device_id, enabled)` - Enable/disable freeze protection
- `set_notification_setting(device_id, enabled)` - Enable/disable notifications
- `set_hold(device_id, enabled)` - Set temporary hold
- `set_permanent_hold(device_id, enabled)` - Set permanent hold

**Example:**
```python
# Turn on device
await client.set_state("12345", 1)  # Replace with your device ID

# Set to 72°F
await client.set_temperature("12345", 72)  # Replace with your device ID

# Enable freeze protection
await client.set_freeze_protect("12345", True)  # Replace with your device ID
```

### 4. Utility Methods

#### Temperature Conversion
- `convert_temperature(temperature, from_unit, to_unit)` - Convert between C and F

**Example:**
```python
# Convert 72°F to Celsius
celsius = client.convert_temperature(72, "F", "C")  # Returns 22.22
```

#### Enhanced Device Info
- `get_device_full_info(device_id)` - Get complete device information including all settings

## Improved Error Handling

The API client now includes:
- Better error messages with API error codes
- Network error handling
- JSON parsing error handling
- Automatic retry on authentication failures
- Detailed logging for debugging

## API Endpoints Discovered

### Working Endpoints
- `GET /device/list` - List all devices
- `GET /device/{id}` - Get device details
- `PATCH /device/update-temperature/{id}` - Update temperature/state
- `GET /schedule/list` - List all schedules
- `POST /schedule/add` - Create schedule (requires proper payload)
- `DELETE /schedule/{id}` - Delete schedule
- `OPTIONS /device/*` - CORS preflight (returns 204)

### Response Structure
All API responses follow this structure:
```json
{
    "status": "success",
    "statusCode": 200,
    "msgCode": 1019,
    "msg": "Device data fetched successfully",
    "data": { ... }
}
```

## Device Data Fields Available

From device detail endpoint, the following fields are available:

### Basic Info
- `id`, `serial_no`, `name`, `location_name`
- `current_temperature`, `ambient_temperature`
- `current_mode`, `device_status`, `state`
- `firmware_version`, `model_no`

### Settings
- `night_light_setting` - Color, brightness, auto mode
- `pilot_light_setting` - Brightness, auto-dim settings
- `display_setting` - Display brightness and timeout
- `child_lock_setting`, `freeze_protect_setting`, `notification_setting`

### Status Flags
- `is_schedule_active`, `is_geofence_active`
- `is_hold`, `is_virtual`
- `signal_strength`, `ssid`

### Schedule Info
- `schedule` - Current schedule data
- `is_schedule_active` - Whether schedule is active
- `last_schedule_temperature` - Last scheduled temp

### Mode Info
- `current_mode`, `previous_mode`
- `mini_split_mode`, `previous_mini_split_mode`

## Temperature Units

Devices can report temperatures in Celsius ("C") or Fahrenheit ("F").
The `temperature_unit` field indicates the unit used.

Use `convert_temperature()` method to convert between units as needed.

## Usage Examples

### Complete Device Control
```python
# Get device info
device = await client.get_device_full_info("12345")  # Replace with your device ID

# Check current settings
night_light = await client.get_night_light_setting("12345")  # Replace with your device ID
print(f"Night light brightness: {night_light['brightness']}")

# Update multiple settings
await client.set_temperature("12345", 72)  # Replace with your device ID
await client.set_state("12345", 1)  # Replace with your device ID
await client.set_freeze_protect("12345", True)  # Replace with your device ID
```

### Schedule Management
```python
# List all schedules
schedules = await client.get_schedule_list()
for schedule in schedules:
    print(f"Schedule: {schedule['name']} (ID: {schedule['id']})")

# Get specific schedule
schedule = await client.get_schedule(1234)  # Replace with your schedule ID
print(f"Schedule data: {schedule['schedule_data']}")
```

## Notes

1. **Temperature Units**: Always check `temperature_unit` field before displaying temperatures
2. **Schedule Payload**: The `create_schedule()` endpoint requires proper payload structure (may need reverse engineering)
3. **Settings Endpoints**: Some settings endpoints may need to be discovered through testing
4. **Error Handling**: All methods now properly handle and log errors
5. **Token Management**: Automatic token refresh is handled transparently

## Future Enhancements

Potential areas for further enhancement:
- Geofence management (endpoints not yet discovered)
- Device grouping functionality
- Historical data/statistics
- Firmware update management
- Device sharing/member management

