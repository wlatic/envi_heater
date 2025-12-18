# How to Create a GitHub Release

## Option 1: Using PowerShell Script (Windows)

1. **Create a GitHub Personal Access Token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Name it: "Release Creation"
   - Select scope: `repo` (full control of private repositories)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)

2. **Run the PowerShell script:**
   ```powershell
   .\create_release.ps1 -Token "your_token_here"
   ```

## Option 2: Using GitHub Web Interface (Easiest)

1. Go to: https://github.com/rendershome/smart_envi/releases/new
2. Select tag: `v2.0.0`
3. Title: `Release v2.0.0 - First Official Release`
4. Description: Copy contents from `RELEASE_NOTES_v2.0.0.md`
5. Click "Publish release"

## Option 3: Using curl (Any Platform)

1. **Create a GitHub Personal Access Token** (see Option 1, step 1)

2. **Run curl command:**
   ```bash
   curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Accept: application/vnd.github+json" \
     -H "X-GitHub-Api-Version: 2022-11-28" \
     -d @- https://api.github.com/repos/rendershome/smart_envi/releases <<EOF
   {
     "tag_name": "v2.0.0",
     "name": "Release v2.0.0 - First Official Release",
     "body": "$(cat RELEASE_NOTES_v2.0.0.md | sed 's/$/\\n/' | tr -d '\n')",
     "draft": false,
     "prerelease": false
   }
   EOF
   ```

## Security Note

⚠️ **Never commit your GitHub token to git!** The token is sensitive and should be kept secret. These scripts use the token only for the API call and don't store it.


