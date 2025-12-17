# Troubleshooting Binary Sensors

## Issue: Binary Sensors Not Appearing

If binary sensors aren't showing up after installation, follow these steps:

### Step 1: Check Home Assistant Logs

1. Go to **Settings** → **System** → **Logs**
2. Look for errors related to `envi_heater` or `binary_sensor`
3. Check for any import errors or setup failures

### Step 2: Verify Files Are Copied Correctly

Ensure these files exist in your `custom_components/envi_heater/` directory:
- `binary_sensor.py` ✓
- `coordinator.py` ✓
- `__init__.py` (should include `Platform.BINARY_SENSOR`) ✓
- `climate.py` ✓
- `api.py` ✓

### Step 3: Check Integration Status

1. Go to **Settings** → **Devices & Services**
2. Find your Envi Heater integration
3. Click on it to see status
4. Check if there are any errors shown

### Step 4: Enable Debug Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.envi_heater: debug
```

Then restart Home Assistant and check logs for:
- "Setting up binary sensors for entry..."
- "Found X devices for binary sensors..."
- "Created X binary sensors for X devices"

### Step 5: Manual Refresh

1. Go to **Developer Tools** → **Services**
2. Find `envi_heater.refresh_all`
3. Call the service
4. Check if binary sensors appear

### Step 6: Reinstall Integration

If sensors still don't appear:

1. Remove the integration (Settings → Devices & Services → Envi Heater → Delete)
2. Restart Home Assistant
3. Re-add the integration
4. Check logs during setup

## Common Issues

### Issue: "Coordinator not found"
**Solution**: The coordinator should be created by the climate platform. Make sure climate entities are loading first.

### Issue: "No devices found"
**Solution**: Check that your Envi account has devices and the API connection is working.

### Issue: Import Errors
**Solution**: Make sure all files are in the correct location and Python syntax is correct.

### Issue: Platform Not Loading
**Solution**: Verify `__init__.py` includes `Platform.BINARY_SENSOR` in the PLATFORMS list.

## Expected Log Output

When binary sensors load successfully, you should see:

```
INFO: Found 3 devices for binary sensors: ['12345', '12346', '12347']
INFO: Created 15 binary sensors for 3 devices
```

## Verification

After installation, you should see:
- 5 binary sensors per device
- Entities named like: `Bedroom Freeze Protection`, `Bedroom Child Lock`, etc.
- Sensors updating every 30 seconds

## Still Not Working?

1. Check the full error in logs
2. Verify coordinator is working (climate entities should update)
3. Try removing and re-adding the integration
4. Check Home Assistant version compatibility

