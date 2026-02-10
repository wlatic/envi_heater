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
3. Search for "Envi Smart Heater" and install

## Option 2: Submit to HACS Default (Recommended for Visibility)

### Requirements Checklist
✅ Public GitHub repository: `https://github.com/rendershome/smart_envi`
✅ Proper structure (`custom_components/smart_envi/`)
✅ `manifest.json` with required fields
✅ `hacs.json` file
✅ GitHub releases (v2.0.0 is latest stable)
✅ README.md with installation instructions
✅ Documentation
✅ GitHub Actions workflows (HACS Action & Hassfest) - **Just added!**

### Steps to Submit

1. **Verify GitHub Actions Pass**
   - Go to: https://github.com/rendershome/smart_envi/actions
   - Push a commit or manually trigger the workflows
   - Ensure both "HACS Action" and "Hassfest" workflows pass ✅
   - If they fail, fix any issues before proceeding

2. **Fork the HACS Default Repository**
   - Go to: https://github.com/hacs/default
   - Click "Fork" (top right)
   - This creates your own copy of the HACS default repository

3. **Add Your Repository**
   - In your fork, navigate to: `integration` folder
   - Open the file (it's a list of repository URLs, one per line)
   - Add your repository URL in alphabetical order:
     ```
     https://github.com/rendershome/smart_envi
     ```
   - Commit the change with message: "Add Smart Envi integration"

4. **Submit Pull Request**
   - Go to your fork on GitHub
   - Click "Pull Request" or "Contribute" → "Open Pull Request"
   - **Title**: `Add Smart Envi integration`
   - **Description**: Use this template:
     ```markdown
     ## Description
     Adds the Smart Envi integration for Home Assistant.
     
     ## Repository
     https://github.com/rendershome/smart_envi
     
     ## Type
     Integration
     
     ## Notes
     - Unofficial integration for Envi Smart Heaters
     - Provides climate control, sensors, and binary sensors
     - Requires Home Assistant 2023.1.0 or later
     - GitHub Actions (HACS Action & Hassfest) are passing ✅
     ```
   - Submit PR

5. **Wait for Review**
   - HACS maintainers will review (usually within a few days to a week)
   - They'll check:
     - Repository structure ✅
     - Code quality ✅
     - Documentation ✅
     - GitHub Actions passing ✅
     - Compliance with HACS standards ✅

### Important Notes

- **Only repository owner** (`@rendershome`) can submit
- **Must have GitHub releases** ✅ (you have v2.0.0)
- **Must pass HACS validation** ✅ (GitHub Actions will verify)
- **May need to add to Home Assistant Brands** (for UI icons) - optional

### After Approval

Once approved:
- ✅ Your integration appears in HACS search
- ✅ Users can install directly without adding custom repository
- ✅ More visibility = more users
- ✅ Still maintainable by you
- ✅ Updates automatically via GitHub releases

## Current Repository Status

✅ **Ready for Submission:**
- Public repository: ✅
- Proper structure: ✅
- manifest.json: ✅ (with documentation/issue_tracker)
- hacs.json: ✅
- GitHub releases: ✅ (v2.0.0 stable)
- README.md: ✅
- Documentation: ✅
- Code quality: ✅
- GitHub Actions: ✅ (HACS Action & Hassfest workflows added)

## Next Steps

1. **Commit and push the GitHub Actions workflows** to your repository
2. **Verify workflows pass** on GitHub Actions page
3. **Fork hacs/default** repository
4. **Add your repo URL** to the integration list
5. **Submit PR** with the description above
6. **Wait for approval** (usually 1-2 weeks)

## Helpful Links

- HACS Documentation: https://hacs.xyz/docs/publish/include/
- HACS Default Repository: https://github.com/hacs/default
- Home Assistant Brands: https://github.com/home-assistant/brands
- HACS Action: https://github.com/hacs/action
- Hassfest: https://github.com/home-assistant/actions

## Troubleshooting

If GitHub Actions fail:
- Check the error messages in the Actions tab
- Common issues:
  - Missing required fields in `manifest.json`
  - Invalid structure
  - Missing `hacs.json`
- Fix issues and push again
