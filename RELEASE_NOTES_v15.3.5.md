# Release v15.3.5 - Schedule Management UI Form

## 🎯 Overview

This release adds a user-friendly UI form for editing heating schedules directly from Home Assistant's configuration interface, eliminating the need to use YAML or Developer Tools.

## ✨ New Features

### Schedule Management UI Form
- **Menu System**: Options flow now includes a menu to choose between integration settings and schedule editing
- **Device Selection**: Easy dropdown selection of which heater to edit
- **Visual Schedule Editor**: Form-based interface for editing schedules with:
  - Enable/Disable toggle
  - Schedule name field
  - Time entries editor with structured format
- **Current Schedule Display**: Automatically loads and displays existing schedule data
- **Validation**: Real-time validation of time formats and temperature ranges

### Enhanced User Experience
- **No YAML Required**: Edit schedules through the UI without writing YAML
- **No Developer Tools Needed**: Access schedule editor from Settings → Devices & Services
- **Intuitive Interface**: Simple form fields instead of complex service calls
- **Error Messages**: Clear validation errors guide users to correct format

## 🔧 How to Use

### Accessing the Schedule Editor

1. Go to **Settings** → **Devices & Services**
2. Find your **Smart Envi** integration
3. Click the **Configure** (gear icon) button
4. Select **"Edit Device Schedule"** from the menu
5. Choose your heater from the dropdown
6. Edit the schedule using the form

### Schedule Format

Time entries use a structured format:
```
HH:MM:SS,temperature,enabled|HH:MM:SS,temperature,enabled
```

**Example:**
```
08:00:00,72,true|12:00:00,70,true|18:00:00,68,true|22:00:00,65,true
```

**Parameters:**
- `HH:MM:SS`: Time in 24-hour format (e.g., `08:00:00`)
- `temperature`: Temperature between 50-86°F
- `enabled`: `true` or `false` to enable/disable this time slot
- `|`: Separator between multiple time entries

### Form Fields

- **Enabled**: Toggle to enable/disable the entire schedule
- **Name**: Optional schedule name (e.g., "Weekday Schedule")
- **Time Entries**: Text field with structured format (see above)

## 📝 Technical Details

### Implementation

- **Multi-Step Flow**: Uses Home Assistant's config flow menu system
- **Direct API Integration**: Calls API client methods directly (no service layer overhead)
- **Automatic Refresh**: Device data refreshes after schedule changes
- **Error Handling**: Comprehensive validation and error messages
- **Backward Compatible**: Existing service-based methods still work

### Files Changed

- `custom_components/smart_envi/config_flow.py`:
  - Added menu system to options flow
  - Added `async_step_select_device` for device selection
  - Added `async_step_edit_schedule` for schedule editing form
  - Integrated with API client for direct schedule management
- `custom_components/smart_envi/manifest.json`: Version bump to 15.3.5

## 🔄 Migration Notes

- **No Breaking Changes**: This is a feature addition
- **No Migration Required**: Existing configurations continue to work
- **Service Methods Still Available**: `smart_envi.set_schedule` and `smart_envi.get_schedule` services remain functional
- **Backward Compatible**: All existing functionality preserved

## 🎓 What This Means for Users

### Before (v15.3.4 and earlier)
- Had to use Developer Tools → Services
- Required YAML knowledge
- Manual service calls with complex data structures
- No visual feedback

### After (v15.3.5)
- ✅ Access from Settings → Devices & Services → Configure
- ✅ Visual form interface
- ✅ No YAML required
- ✅ Clear validation and error messages
- ✅ Current schedule automatically loaded

### Benefits

- **Easier to Use**: Non-technical users can now edit schedules
- **Faster Workflow**: No need to look up service syntax
- **Better UX**: Visual feedback and validation
- **Less Error-Prone**: Form validation prevents common mistakes

## ⚠️ Important Notes

- **Time Format**: Must use `HH:MM:SS` format (e.g., `08:00:00`, not `8:00`)
- **Temperature Range**: Temperatures must be between 50-86°F
- **Multiple Entries**: Separate multiple time entries with `|`
- **Service Methods**: The service-based methods (`smart_envi.set_schedule`, `smart_envi.get_schedule`) still work for automation/script use

## 🙏 Credits

- **Current Maintainer**: [@rendershome](https://github.com/rendershome)

---

**Full Changelog**: 
- Commit: Add UI form for schedule management in options flow

