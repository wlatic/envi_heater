# Guide: Creating a GitHub Pull Request

This guide will help you create a pull request for the enhanced Envi Heater integration.

## Prerequisites

1. GitHub account
2. Git installed on your system
3. Access to the original repository (or fork it first)

## Step 1: Initialize Git Repository

If this isn't already a git repository, initialize it:

```bash
cd envi_heater-0.14.1-mod
git init
```

## Step 2: Add All Files

```bash
git add .
```

## Step 3: Create Initial Commit

```bash
git commit -m "feat: Enhanced Envi Heater integration with comprehensive monitoring

- Added DataUpdateCoordinator for efficient polling (~66% reduction in API calls)
- Added 16 entities per device (1 climate + 5 binary sensors + 10 sensors)
- Enhanced API client with 20+ new methods
- Added comprehensive device monitoring
- Improved UI with dynamic icons and proper entity categories
- Added 7 custom services for advanced control
- Removed switch platform (settings are read-only via API)
- Added extensive documentation"
```

## Step 4: Add Remote Repository

If you're contributing to an existing repository:

```bash
# Add the original repository as upstream
git remote add upstream https://github.com/wlatic/envi_heater.git

# Add your fork as origin (replace with your username)
git remote add origin https://github.com/YOUR_USERNAME/envi_heater.git
```

## Step 5: Create a New Branch

```bash
git checkout -b enhance/envi-heater-comprehensive-monitoring
```

Or if you prefer a shorter name:

```bash
git checkout -b feat/enhanced-monitoring
```

## Step 6: Push to Your Fork

```bash
git push -u origin enhance/envi-heater-comprehensive-monitoring
```

## Step 7: Create Pull Request on GitHub

1. Go to the original repository on GitHub
2. You should see a banner suggesting to create a pull request
3. Click "Compare & pull request"
4. Use the content from `PR_DESCRIPTION.md` or `PULL_REQUEST_TEMPLATE.md` as your PR description
5. Add any screenshots if available
6. Click "Create pull request"

## Alternative: If Starting Fresh

If you're creating a completely new repository:

```bash
# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Enhanced Envi Heater integration"

# Create repository on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/envi_heater.git
git branch -M main
git push -u origin main
```

## Commit Message Format

Following conventional commits:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

## Files to Review Before PR

- [ ] `.gitignore` - Excludes sensitive files
- [ ] `README.md` - Updated with new features
- [ ] `CHANGELOG.md` - Documents all changes
- [ ] `manifest.json` - Version updated
- [ ] No hardcoded credentials
- [ ] No test files with real credentials
- [ ] Documentation is complete

## PR Checklist

Before submitting, ensure:

- [x] Code follows Home Assistant style guidelines
- [x] All entities properly categorized
- [x] Error handling implemented
- [x] Coordinator pattern used correctly
- [x] Documentation updated
- [x] No breaking changes
- [x] Backward compatible
- [x] No sensitive data in code
- [x] Test files excluded (if they contain credentials)

## Useful Git Commands

```bash
# Check status
git status

# View changes
git diff

# View commit history
git log --oneline

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Create a new commit with updated files
git add .
git commit --amend -m "Updated commit message"
```

## Troubleshooting

### If you need to update the PR:

```bash
# Make your changes
git add .
git commit -m "fix: Description of fix"
git push
```

The PR will automatically update.

### If you need to rebase:

```bash
git fetch upstream
git rebase upstream/main
git push --force-with-lease
```

---

**Note**: Replace `YOUR_USERNAME` and repository URLs with your actual GitHub username and repository URLs.


