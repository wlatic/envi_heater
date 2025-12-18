# Release v15.3.4 - Schedule Management Enhancement

## 🎯 Overview

This release adds a new service to retrieve schedule information, making it much easier to view and edit heating schedules in Home Assistant.

## ✨ New Features

### Get Schedule Service
- **New Service**: `smart_envi.get_schedule` - Retrieve current schedule details for any heater
- **Schedule Information**: Returns schedule_id, enabled status, name, temperature, and all time entries
- **Better UX**: Users can now view existing schedules before editing them
- **Complete Schedule Data**: Provides full schedule structure including all time slots

## 🔧 Improvements

### Enhanced Schedule Editing Workflow
1. **View Current Schedule**: Use `smart_envi.get_schedule` to see what's configured
2. **Edit Schedule**: Modify the schedule data as needed
3. **Update Schedule**: Use `smart_envi.set_schedule` to apply changes

### Documentation Updates
- **Comprehensive Guide**: Updated README with detailed schedule editing instructions
- **Examples**: Added complete workflow examples for schedule management
- **Service Documentation**: Documented all schedule-related services

## 📝 Technical Details

### New Service: `smart_envi.get_schedule`

**Usage:**
```yaml
service: smart_envi.get_schedule
data:
  entity_id: climate.smart_envi_12345
```

**Response:**
```yaml
schedule_id: 12345
device_id: "abc123"
enabled: true
name: "My Schedule"
temperature: 72
times:
  - time: "08:00:00"
    temperature: 72
    enabled: true
  - time: "18:00:00"
    temperature: 68
    enabled: true
```

### Service Integration
- Automatically detects existing schedules via `schedule_id`
- Fetches full schedule details from API when available
- Falls back to device state schedule info if needed
- Returns complete schedule structure for easy editing

## 🔄 Migration Notes

- **No Breaking Changes**: This is a feature addition
- **No Migration Required**: Existing configurations continue to work
- **Backward Compatible**: All existing services remain unchanged

## 🎓 What This Means for Users

### Easier Schedule Management
- **View Before Edit**: See current schedule configuration before making changes
- **Complete Information**: Get all schedule details including all time entries
- **Better Workflow**: Natural workflow of view → edit → update

### Improved User Experience
- **No Guesswork**: Know exactly what schedule is configured
- **Easier Troubleshooting**: Check schedule status and details
- **Better Automation**: Use schedule data in automations and scripts

## 📋 Files Changed

- `custom_components/smart_envi/services.py`: Added `get_heater_schedule` service function
- `custom_components/smart_envi/README.md`: Updated with schedule editing documentation
- `custom_components/smart_envi/manifest.json`: Version bump to 15.3.4

## 🙏 Credits

- **Current Maintainer**: [@rendershome](https://github.com/rendershome)

---

**Full Changelog**: 
- Commit `ecd462d`: Add get_schedule service for easier schedule editing

