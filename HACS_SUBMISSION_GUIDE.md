# HACS Submission Guide

## Current Status
✅ Your integration already works as a **Custom Repository** in HACS
- Users can add it manually via: HACS → Integrations → Custom repositories
- Repository URL: `https://github.com/rendershome/smart_envi`

## Option 1: Keep as Custom Repository (Current)
**Pros:**
- Already working
- No approval needed
- Full control

**Cons:**
- Users must manually add repository URL
- Less discoverable
- Not in HACS search

**How users install:**
1. HACS → Integrations → ⋮ → Custom repositories
2. Add: `https://github.com/rendershome/smart_envi`
3. Search for "Envi Smart Heater"
4. Install

## Option 2: Submit to HACS Default (Recommended for Visibility)

### Requirements Checklist
✅ Public GitHub repository
✅ Proper structure (`custom_components/smart_envi/`)
✅ `manifest.json` with required fields (updated)
✅ `hacs.json` file (exists)
✅ GitHub releases (v15.0, v15.1, v15.2, v15.2.1)
✅ README.md with installation instructions
✅ Documentation

### Steps to Submit

1. **Fork the HACS Default Repository**
   - Go to: https://github.com/hacs/default
   - Click "Fork" (top right)

2. **Add Your Repository**
   - In your fork, navigate to: `integration` folder
   - Open the file (it's a list of repositories)
   - Add your repository URL in alphabetical order:
     ```
     https://github.com/rendershome/smart_envi
     ```
   - Commit the change

3. **Submit Pull Request**
   - Go to your fork on GitHub
   - Click "Pull Request"
   - Title: "Add Smart Envi integration"
   - Description: Include:
     - Brief description of the integration
     - Link to repository
     - Note that it's an unofficial integration
   - Submit PR

4. **Wait for Review**
   - HACS maintainers will review
   - May take a few days/weeks
   - They'll check:
     - Repository structure
     - Code quality
     - Documentation
     - Compliance with HACS standards

### Important Notes

- **Only repository owner or major contributor** can submit
- **Must have GitHub releases** (you have these ✅)
- **Must pass HACS validation** (automated checks)
- **May need to add to Home Assistant Brands** (for UI icons)

### After Approval

Once approved:
- Your integration appears in HACS search
- Users can install directly without adding custom repository
- More visibility = more users
- Still maintainable by you

## Current Repository Status

✅ **Ready for Submission:**
- Public repository: ✅
- Proper structure: ✅
- manifest.json: ✅ (updated with documentation/issue_tracker)
- hacs.json: ✅
- GitHub releases: ✅
- README.md: ✅
- Documentation: ✅
- Code quality: ✅

## Next Steps

1. **Decide**: Custom repository (current) or submit to default?
2. **If submitting**: Follow steps above to create PR
3. **If staying custom**: Update documentation to make it clear how to add

## Helpful Links

- HACS Documentation: https://www.hacs.xyz/docs/publish/include/
- HACS Default Repository: https://github.com/hacs/default
- Home Assistant Brands: https://github.com/home-assistant/brands


