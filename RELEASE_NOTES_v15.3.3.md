# Release v15.3.3 - Repository Sanitization & Code Quality

## 🎯 Overview

This release focuses on repository sanitization, ensuring no test scripts or sensitive data are tracked in git, and includes minor code quality improvements.

## ✨ Changes

### Repository Sanitization
- **Test Scripts Excluded**: All test scripts (`test_*.py`, `*_test.py`, `test_api*.py`) are now excluded from git tracking
- **Sensitive Data Protection**: Enhanced `.gitignore` to exclude credentials, secrets, and environment files
- **Cache Files Removed**: Removed `__pycache__` files from repository tracking
- **Clean Repository**: Repository is now sanitized and safe for public GitHub hosting

### Code Quality
- **Validation Script**: Added local validation test script for code quality checks (kept local only)
- **Schedule Service**: Minor improvements to schedule service implementation
- **Better Organization**: Improved project structure and file organization

## 🔒 Security Improvements

### Enhanced `.gitignore`
The `.gitignore` file now includes comprehensive patterns to prevent accidental commits of:
- Test scripts (may contain credentials)
- Environment files (`*.env`, `.env.*`)
- Secret files (`secrets.yaml`, `secrets.json`)
- Credential files (`*credentials*`, `*password*`, `*secret*`)
- Python cache files (`__pycache__/`)

### Repository Cleanup
- Removed `test_validation.py` from git tracking (now local only)
- Removed `__pycache__` directories from tracking
- Verified no credentials or sensitive data exist in tracked files

## 📝 Technical Details

### Files Changed
- `.gitignore`: Enhanced with comprehensive exclusion patterns
- `manifest.json`: Version bump to 15.3.3
- Repository cleanup: Removed test scripts and cache files from tracking

### Commits Included
- `45189fd`: Sanitize repository: exclude test scripts and sensitive data from git
- `c8b6357`: Add validation test script for code quality checks
- `ddc4624`: Add .gitignore and improve schedule service implementation
- `fd290d4`: Add empty services.yaml as workaround for HA 2025.12 service discovery check

## 🔄 Migration Notes

- **No Breaking Changes**: This is a maintenance release
- **No Migration Required**: Existing configurations continue to work
- **No User Impact**: Changes are internal repository improvements only

## 🎓 What This Means for Users

### Better Security
- Repository is now properly sanitized
- No risk of accidentally committing credentials or test data
- Safe for public GitHub hosting

### Better Development Practices
- Test scripts remain local for development
- Cleaner repository structure
- Better separation between development and production code

## ⚠️ Important Notes

- **Test Scripts**: All test scripts are now local-only and will not be included in releases
- **Development**: Test scripts can still be used locally for development and testing
- **No Functionality Changes**: This release does not change any integration functionality

## 🙏 Credits

- **Current Maintainer**: [@rendershome](https://github.com/rendershome)

---

**Full Changelog**: 
- Commit `45189fd`: Sanitize repository: exclude test scripts and sensitive data from git
- Commit `c8b6357`: Add validation test script for code quality checks
- Commit `ddc4624`: Add .gitignore and improve schedule service implementation
- Commit `fd290d4`: Add empty services.yaml as workaround for HA 2025.12 service discovery check

