# Sensors Implementation

## Overview

Added 5 sensors for each Envi heater device to provide detailed device information and monitoring capabilities.

## Sensors Created

### 1. Signal Strength (`sensor.envi_heater_{device_id}_signal_strength`)
- **Unit**: Percentage (%)
- **State Class**: Measurement
- **Icon**: `mdi:signal`
- **Purpose**: Shows WiFi signal strength
- **Data Source**: `signal_strength` from device data (0-100)
- **Use Case**: Monitor device connectivity, troubleshoot WiFi issues

### 2. Firmware Version (`sensor.envi_heater_{device_id}_firmware_version`)
- **Unit**: None (text)
- **Icon**: `mdi:chip`
- **Purpose**: Shows device firmware version
- **Data Source**: `firmware_version` from device data
- **Use Case**: Track firmware versions, identify devices needing updates

### 3. Mode (`sensor.envi_heater_{device_id}_mode`)
- **Unit**: None (text)
- **Icon**: `mdi:thermostat`
- **Purpose**: Shows current device mode
- **Data Source**: `current_mode` from device data
- **Values**: "Heat" (mode 1), "Auto" (mode 3), or "Mode X" for unknown modes
- **Attributes**: `mode_number` - Raw mode number
- **Use Case**: Monitor device mode, debug mode changes

### 4. Schedule Name (`sensor.envi_heater_{device_id}_schedule_name`)
- **Unit**: None (text)
- **Icon**: `mdi:calendar-clock`
- **Purpose**: Shows name of active schedule
- **Data Source**: `schedule.name` or `schedule.title` from device data
- **Attributes**: 
  - `schedule_id` - Schedule ID
  - `temperature` - Scheduled temperature
  - `trigger_time` - Schedule trigger time
  - `day` - Day of week
- **Use Case**: See which schedule is active, verify schedule is running

### 5. Schedule Temperature (`sensor.envi_heater_{device_id}_schedule_temperature`)
- **Unit**: Fahrenheit (°F)
- **State Class**: Measurement
- **Icon**: `mdi:thermometer`
- **Purpose**: Shows scheduled temperature
- **Data Source**: `schedule.temperature` from device data
- **Note**: Automatically converts from Celsius if device uses Celsius
- **Use Case**: Monitor scheduled temperature, verify schedule settings

## Entity Names

Entities are named using the device name from the API:
- `Bedroom Signal Strength`
- `Bedroom Firmware Version`
- `Bedroom Mode`
- `Bedroom Schedule Name`
- `Bedroom Schedule Temperature`

## Integration with Coordinator

All sensors:
- Use the same `EnviDataUpdateCoordinator` as climate entities
- Update automatically when coordinator fetches new data
- No additional API calls required
- Update every 30 seconds (coordinator interval)

## Usage Examples

### Automation: Alert on Low Signal Strength

```yaml
automation:
  - alias: "Low WiFi Signal Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.bedroom_signal_strength
        below: 50
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          message: "Bedroom heater WiFi signal is low ({{ states('sensor.bedroom_signal_strength') }}%)"
```

### Automation: Notify on Mode Change

```yaml
automation:
  - alias: "Mode Changed"
    trigger:
      - platform: state
        entity_id: sensor.bedroom_mode
    action:
      - service: notify.mobile_app
        data:
          message: "Bedroom heater mode changed to {{ states('sensor.bedroom_mode') }}"
```

### Dashboard Card Example

```yaml
type: entities
title: Bedroom Heater Info
entities:
  - entity: climate.bedroom
  - entity: sensor.bedroom_signal_strength
  - entity: sensor.bedroom_firmware_version
  - entity: sensor.bedroom_mode
  - entity: sensor.bedroom_schedule_name
  - entity: sensor.bedroom_schedule_temperature
```

### Template Sensor: Device Health Score

```yaml
template:
  - sensor:
      - name: "Bedroom Heater Health"
        state: >
          {% set signal = states('sensor.bedroom_signal_strength') | int %}
          {% if signal > 75 %}
            Excellent
          {% elif signal > 50 %}
            Good
          {% elif signal > 25 %}
            Fair
          {% else %}
            Poor
          {% endif %}
```

## Mode Values

Current mode mapping:
- **Mode 1**: Heat
- **Mode 3**: Auto
- **Other modes**: Displayed as "Mode X" (where X is the mode number)

If you discover other mode values, they can be added to the `MODE_MAP` in `sensor.py`.

## Benefits

1. **Monitoring**: Track device health and connectivity
2. **Debugging**: Identify issues with signal strength or firmware
3. **Automations**: Create automations based on device state
4. **Visibility**: See schedule information at a glance
5. **Efficient**: Uses coordinator data (no extra API calls)

## Entity Count

For each heater device, you now get:
- 1 Climate entity
- 5 Binary sensors
- 5 Sensors
- **Total: 11 entities per device**

With 3 devices = 33 entities total

## Future Enhancements

Potential additional sensors:
- `sensor.envi_heater_wifi_ssid` - WiFi network name
- `sensor.envi_heater_last_update` - Last update timestamp
- `sensor.envi_heater_location` - Device location name
- `sensor.envi_heater_model` - Device model number
- `sensor.envi_heater_serial` - Serial number

## Testing

After installation, verify:
- [ ] All 5 sensors appear for each device
- [ ] Signal strength shows correct percentage
- [ ] Firmware version displays correctly
- [ ] Mode shows correct mode name
- [ ] Schedule name shows active schedule (or "None")
- [ ] Schedule temperature shows correct value
- [ ] Sensors update when device state changes
- [ ] Temperature conversion works for Celsius devices


