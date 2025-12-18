# Release v15.2 - Reliability Improvements and Official Disclaimers

## Major Improvements

### Retry Logic with Exponential Backoff
- Automatic retry for transient network errors (up to 3 attempts)
- Exponential backoff delays: 1s, 2s, 4s (max 30s)
- Retries for server errors (500, 502, 503, 504)
- Better handling of network timeouts and connection errors

### Rate Limiting Protection
- Detects HTTP 429 (Too Many Requests) responses
- Respects `Retry-After` header from API
- Automatic backoff when rate limited
- Prevents API bans during high activity

### Data Validation
- Validates API response structure before processing
- Enhanced validation for device list responses
- Better handling of invalid or malformed data
- Prevents crashes from unexpected API changes

### Improved Error Recovery
- Better coordinator error handling
- Per-device error recovery with cached data fallback
- Enhanced logging with full context
- Graceful degradation when devices temporarily fail

## Product Information Updates

### Manufacturer Attribution
- Updated manufacturer to **EHEAT, Inc.** (https://www.eheat.com/)
- Updated configuration URLs to manufacturer website
- Proper attribution throughout integration

### Product Name
- Updated product name to **"Smart Envi"** throughout
- Consistent naming in device info, logs, and documentation
- Updated default device names and model names

## Legal & Documentation

### Official Disclaimers
- Added prominent disclaimers about unofficial status
- Clarified that integration is NOT endorsed by EHEAT/Envi
- Added "use at your own risk" warnings
- Documented API dependency risks

### Documentation Updates
- Updated all README files with disclaimers
- Added manufacturer information
- Improved product attribution
- Better user awareness of integration status

## Technical Details

### Retry Configuration
- `MAX_RETRIES = 3`
- `INITIAL_RETRY_DELAY = 1` second
- `MAX_RETRY_DELAY = 30` seconds
- Retryable status codes: 429, 500, 502, 503, 504

### Validation Improvements
- Response structure validation
- Device list format validation
- Device data integrity checks
- Better error messages for invalid data

## No Breaking Changes
This is a maintenance and reliability release. All existing functionality remains the same. The integration is now more robust and includes proper legal disclaimers.

## Migration Notes
- No migration required
- Existing configurations continue to work
- Users will see updated manufacturer/product names in device info
- Disclaimers are informational only

