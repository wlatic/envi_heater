# Release v15.3.9 - Proper Help Text Display in UI

## 🎯 Overview

This release adds proper help text to the Home Assistant UI by creating a `strings.json` file. Help text now appears when clicking the ? icons in the options flow.

## ✨ New: strings.json for UI Text

Home Assistant uses `strings.json` for displaying help text in the UI, not voluptuous schema descriptions. This release adds proper support.

### Integration Options Help (? icon shows):

**Polling Interval:**
- How often to check for device updates
- Default: 30 seconds (recommended)
- Range: 10-300 seconds
- Lower values = more frequent updates but higher API usage
- Higher values = less API usage but slower response to changes
- Minimum 10 seconds to avoid API rate limiting

**API Timeout:**
- Maximum time to wait for API responses
- Default: 15 seconds (recommended)
- Range: 5-60 seconds
- Increase if you have slow internet or frequent timeout errors
- Decrease if you want faster failure detection

### Schedule Editor Help (? icon shows):

**Enable Schedule:**
- Turn the schedule on or off
- When disabled, the schedule will not run

**Schedule Name:**
- Optional name for this schedule
- Examples: 'Weekday Schedule', 'Weekend Schedule'

**Time Entries:** (with comprehensive examples)
- Format: `HH:MM:SS,temperature,enabled`
- Separate multiple entries with `|` (pipe character)
- Temperature range: 50-86°F
- Enabled: true or false

**Sample Schedules Included:**
```
Morning/Evening:
07:00:00,72,true|22:00:00,68,true

Work Day (away during day):
06:00:00,70,true|08:00:00,62,true|17:00:00,70,true|22:00:00,65,true

Weekend (sleep in):
08:00:00,70,true|23:00:00,68,true

All Day Comfort:
00:00:00,70,true
```

## 🔧 Technical Changes

### Added
- `custom_components/smart_envi/strings.json` - Complete UI text and help descriptions

### Changed
- Cleaned up `config_flow.py` - Removed unused `description` parameters from voluptuous schemas
- Help text now properly displays via Home Assistant's localization system

### How It Works
Home Assistant reads `strings.json` and displays:
- `data` - Field labels
- `data_description` - Help text shown when clicking ? icons
- `description` - Form-level descriptions

## 🎓 User Experience

### Before
- Clicking ? icons linked to GitHub
- No inline help text visible
- Users had to search documentation

### After
- ✅ Clicking ? icons shows detailed help text
- ✅ All help is inline in the UI
- ✅ Sample schedules included
- ✅ No need to visit external documentation

## 📝 Migration Notes

- **No Breaking Changes**
- **Restart Required**: Restart Home Assistant after updating
- Help text appears automatically after restart

---

**Full Changelog**: 
- Commit: Add strings.json for proper UI help text display

