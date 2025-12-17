# Binary Sensors Implementation

## Overview

Added 5 binary sensors for each Envi heater device to provide visibility into device states and settings.

## Binary Sensors Created

### 1. Freeze Protection (`binary_sensor.envi_heater_{device_id}_freeze_protect`)
- **Device Class**: `safety`
- **Purpose**: Shows if freeze protection is enabled
- **Data Source**: `freeze_protect_setting` from device data
- **Use Case**: Monitor freeze protection status, create automations

### 2. Child Lock (`binary_sensor.envi_heater_{device_id}_child_lock`)
- **Device Class**: `lock`
- **Purpose**: Shows if child lock is enabled
- **Data Source**: `child_lock_setting` from device data
- **Use Case**: Monitor child lock status, safety monitoring

### 3. Schedule Active (`binary_sensor.envi_heater_{device_id}_schedule_active`)
- **Device Class**: `running`
- **Purpose**: Shows if schedule is currently active
- **Data Source**: `is_schedule_active` from device data
- **Use Case**: Monitor schedule status, verify schedules are working

### 4. Hold (`binary_sensor.envi_heater_{device_id}_hold`)
- **Device Class**: `running`
- **Purpose**: Shows if temporary hold is active
- **Data Source**: `is_hold` from device data
- **Use Case**: Monitor hold status, detect when schedule is overridden

### 5. Online (`binary_sensor.envi_heater_{device_id}_online`)
- **Device Class**: `connectivity`
- **Purpose**: Shows if device is online and responding
- **Data Source**: `device_status` and coordinator update success
- **Use Case**: Monitor device connectivity, alert on offline devices

## Entity Names

Entities are named using the device name from the API:
- `Bedroom Freeze Protection`
- `Bedroom Child Lock`
- `Bedroom Schedule Active`
- `Bedroom Hold`
- `Bedroom Online`

## Integration with Coordinator

All binary sensors:
- Use the same `EnviDataUpdateCoordinator` as climate entities
- Update automatically when coordinator fetches new data
- No additional API calls required
- Update every 30 seconds (coordinator interval)

## Usage Examples

### Automation: Alert on Freeze Protection Disabled

```yaml
automation:
  - alias: "Alert if Freeze Protection Disabled"
    trigger:
      - platform: state
        entity_id: binary_sensor.bedroom_freeze_protection
        to: "off"
    action:
      - service: notify.mobile_app
        data:
          message: "Freeze protection disabled on Bedroom heater!"
```

### Automation: Notify When Schedule Starts

```yaml
automation:
  - alias: "Schedule Started"
    trigger:
      - platform: state
        entity_id: binary_sensor.bedroom_schedule_active
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          message: "Bedroom heater schedule activated"
```

### Automation: Alert on Device Offline

```yaml
automation:
  - alias: "Heater Offline Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.bedroom_online
        to: "off"
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          message: "Bedroom heater has been offline for 5 minutes!"
```

### Dashboard Card Example

```yaml
type: entities
title: Bedroom Heater Status
entities:
  - entity: climate.bedroom
  - entity: binary_sensor.bedroom_freeze_protection
  - entity: binary_sensor.bedroom_child_lock
  - entity: binary_sensor.bedroom_schedule_active
  - entity: binary_sensor.bedroom_hold
  - entity: binary_sensor.bedroom_online
```

## Benefits

1. **Visibility**: See device states at a glance
2. **Automations**: Create automations based on device states
3. **Monitoring**: Track device health and settings
4. **No Extra API Calls**: Uses coordinator data (efficient)
5. **Real-time Updates**: Updates every 30 seconds automatically

## Entity Count

For each heater device, you get:
- 1 Climate entity
- 5 Binary sensors
- **Total: 6 entities per device**

With 3 devices = 18 entities total

## Device Classes

Device classes provide:
- **Proper icons** in Home Assistant UI
- **Better organization** in device view
- **Semantic meaning** for automations

## Future Enhancements

Potential additional binary sensors:
- `geofence_active` - If geofence is active
- `notification_enabled` - Notification setting status
- `permanent_hold` - Permanent hold status (if different from temporary hold)

## Testing

After installation, verify:
- [ ] All 5 binary sensors appear for each device
- [ ] Sensors update when device state changes
- [ ] Freeze protection sensor reflects actual setting
- [ ] Child lock sensor reflects actual setting
- [ ] Schedule active sensor updates when schedule runs
- [ ] Hold sensor updates when hold is set/cleared
- [ ] Online sensor shows correct connectivity status

