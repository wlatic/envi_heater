# API Limitations

## Read-Only Settings

The Envi API has limitations on which device settings can be changed through the API. The following settings are **read-only** and can only be changed through the Envi mobile app:

### Settings That Cannot Be Changed via API

1. **Freeze Protection** (`freeze_protect_setting`)
   - Error: "freeze_protect_setting is not allowed"
   - Can only be changed via mobile app

2. **Child Lock** (`child_lock_setting`)
   - Error: "child_lock_setting is not allowed"
   - Can only be changed via mobile app

3. **Notifications** (`notification_setting`)
   - Error: "notification_setting is not allowed"
   - Can only be changed via mobile app

4. **Hold** (`is_hold`)
   - Error: "is_hold is not allowed"
   - Can only be changed via mobile app

5. **Permanent Hold** (`permanent_hold`)
   - Error: "permanent_hold is not allowed"
   - Can only be changed via mobile app

### Settings That CAN Be Changed via API

The following settings **can** be changed through the API:

1. **Temperature** (`temperature`)
   - Endpoint: `PATCH /device/update-temperature/{device_id}`
   - Works: ✅

2. **State** (`state`) - On/Off
   - Endpoint: `PATCH /device/update-temperature/{device_id}`
   - Works: ✅

3. **Mode** (`mode`) - Heat/Auto/etc.
   - Endpoint: `PATCH /device/update-temperature/{device_id}`
   - Works: ✅

## Implementation Details

### Switches

**Switches have been removed** for read-only settings since they cannot be controlled through the API. Only controllable settings (temperature, state, mode) are available through the climate entity.

### Binary Sensors

All settings are available as binary sensors for monitoring and automation purposes:
- Freeze Protection status
- Child Lock status
- Notification settings
- Hold status
- Schedule Active status
- Online status

These binary sensors allow you to monitor device state and create automations based on current settings, even though the settings themselves cannot be changed through Home Assistant.

## Testing

To verify which controls work, run:
```bash
python test_all_controls.py <username> <password>
```

This will test all controls and show which ones can be updated through the API.

## Future Considerations

If Envi adds API support for these settings in the future, the integration can be updated to enable control for these switches. The current implementation is designed to gracefully handle this limitation while still providing visibility into device state.

