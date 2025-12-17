# Envi API Scanner

A standalone test utility to explore and scan the Envi API endpoints.

## Features

- ✅ Tests all known endpoints from the codebase
- 🔍 Scans for common REST API endpoint patterns
- 🎛️ Tests update/control endpoints
- 🔬 Explores response structures in detail
- 📊 Provides detailed output of API responses

## Installation

```bash
pip install -r requirements-scanner.txt
```

## Usage

```bash
python test_api_scanner.py <username> <password>
```

### Example

```bash
python test_api_scanner.py user@example.com mypassword
```

## What It Does

The scanner performs several types of tests:

1. **Known Endpoints**: Tests endpoints already implemented in the codebase:
   - `GET /device/list` - List all devices
   - `GET /device/{device_id}` - Get device state

2. **Common Patterns**: Tries common REST API patterns:
   - Device status/info/details endpoints
   - Schedule endpoints
   - Settings/config endpoints
   - User/account endpoints
   - Alternative update methods (PUT, POST)

3. **Update Endpoints**: Tests various ways to update device state:
   - Known `PATCH /device/update-temperature/{device_id}`
   - Alternative patterns like `PATCH /device/{device_id}`

4. **Response Analysis**: Deep dives into response structures to understand:
   - Available fields
   - Data types
   - Nested structures

## Output

The scanner provides color-coded output:
- ✅ Success (200 OK)
- 🔒 Authentication required (401/403)
- ❌ Not found (404)
- ⚠️ Other status codes or errors

## Safety

- The scanner uses read-only operations where possible
- Update tests use current device values to avoid changes
- All requests are logged for review

## Use Cases

- Discovering new API endpoints
- Understanding response structures
- Testing authentication
- Debugging API issues
- Finding undocumented features

