# DataUpdateCoordinator Implementation

## Overview

The integration now uses Home Assistant's `DataUpdateCoordinator` pattern for efficient, centralized data updates.

## What Changed

### Before (Individual Polling)
- Each climate entity polled the API independently
- With 3 devices = 3 API calls every update cycle
- No coordination between entities
- Potential race conditions

### After (Coordinated Updates)
- Single coordinator fetches all device data
- With 3 devices = 1 API call per update cycle
- All entities update from same data source
- Better error handling and retry logic

## Benefits

1. **Performance**: Reduced API calls by ~66% (3 devices) or more
2. **Efficiency**: Single coordinated update instead of N individual polls
3. **Reliability**: Better error handling at coordinator level
4. **Consistency**: All entities see the same data snapshot
5. **Scalability**: Easy to add more entities without performance impact

## Implementation Details

### Coordinator (`coordinator.py`)

- **Update Interval**: 30 seconds (configurable)
- **Error Handling**: Graceful degradation - keeps previous data on errors
- **Device Management**: Tracks device IDs and fetches data for all devices
- **Manual Refresh**: Supports refreshing individual devices

### Climate Entity (`climate.py`)

- **Inherits**: `CoordinatorEntity` + `ClimateEntity`
- **Updates**: Automatically receives updates from coordinator
- **Manual Actions**: Refreshes device data immediately after state changes
- **No Polling**: Removed `should_poll` - coordinator handles updates

### Setup (`__init__.py`)

- **Coordinator Creation**: One coordinator per config entry
- **Initial Fetch**: Coordinator fetches data before entities are created
- **Cleanup**: Coordinator is properly cleaned up on unload

## Update Flow

```
┌─────────────────┐
│  Coordinator    │
│  (30s interval) │
└────────┬────────┘
         │
         │ Fetches all devices
         ▼
┌─────────────────┐
│   API Client    │
│  (1 API call)   │
└────────┬────────┘
         │
         │ Returns device data
         ▼
┌─────────────────┐
│   Coordinator   │
│  (stores data)  │
└────────┬────────┘
         │
         │ Notifies listeners
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Entity 1       │     │  Entity 2        │     │  Entity 3       │
│  (Bedroom)      │     │  (Office)        │     │  (Small Bath)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Manual Refresh

When a user action occurs (set temperature, turn on/off), the entity:
1. Calls API to update device
2. Immediately refreshes that device's data from coordinator
3. Updates entity state
4. Next coordinator update will include the change

## Error Handling

### Coordinator Level
- **Network Errors**: Logged, previous data retained
- **Auth Errors**: Raised as UpdateFailed, entities become unavailable
- **Device Errors**: Logged per device, other devices continue updating

### Entity Level
- **Availability**: Based on coordinator success and device data presence
- **State Updates**: Only when coordinator has valid data

## Configuration

Update interval is set in `coordinator.py`:
```python
SCAN_INTERVAL = timedelta(seconds=30)
```

To change:
1. Modify `SCAN_INTERVAL` constant
2. Restart Home Assistant

## Testing

### Verify Coordinator Works
1. Check logs for "Fetched X device IDs"
2. Check logs for coordinator updates every 30 seconds
3. Verify only 1 API call per update cycle (check network tab)

### Verify Entities Update
1. Change temperature in Envi app
2. Wait up to 30 seconds
3. Verify Home Assistant entity updates automatically

### Verify Manual Refresh
1. Set temperature via Home Assistant
2. Check logs for "Refreshed device" message
3. Verify entity state updates immediately

## Performance Metrics

### Before (3 devices)
- API calls per minute: 6 (2 per device)
- Update latency: Variable (each entity polls independently)
- Error handling: Per-entity

### After (3 devices)
- API calls per minute: 2 (coordinated)
- Update latency: Consistent (all entities update together)
- Error handling: Centralized

**Improvement**: ~66% reduction in API calls

## Future Enhancements

1. **Configurable Interval**: Add option in config flow
2. **Adaptive Interval**: Slow down when no changes detected
3. **Webhook Support**: If API supports it, eliminate polling entirely
4. **Batch Updates**: Group multiple device updates into single API call

## Troubleshooting

### Entities Not Updating
- Check coordinator logs for errors
- Verify coordinator is running (check `hass.data[DOMAIN]`)
- Check API connection status

### High API Usage
- Verify coordinator is working (should see single call per cycle)
- Check for multiple coordinators (should be one per config entry)
- Review update interval (default 30s is reasonable)

### Stale Data
- Coordinator keeps previous data on errors (by design)
- Check logs for API errors
- Use `envi_heater.refresh_all` service to force update

