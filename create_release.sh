#!/bin/bash
# Bash script to create GitHub release using Personal Access Token
# Usage: ./create_release.sh YOUR_GITHUB_TOKEN

if [ -z "$1" ]; then
    echo "Error: GitHub token required"
    echo "Usage: ./create_release.sh YOUR_GITHUB_TOKEN"
    exit 1
fi

TOKEN="$1"
REPO="rendershome/smart_envi"
TAG="v2.0.0"
TITLE="Release v2.0.0 - First Official Release"

# Read release notes
RELEASE_NOTES=$(cat RELEASE_NOTES_v2.0.0.md)

# Create JSON payload
JSON=$(cat <<EOF
{
  "tag_name": "$TAG",
  "name": "$TITLE",
  "body": $(echo "$RELEASE_NOTES" | jq -Rs .),
  "draft": false,
  "prerelease": false
}
EOF
)

# Create release via GitHub API
echo "Creating GitHub release for $TAG..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Content-Type: application/json" \
  -d "$JSON" \
  "https://api.github.com/repos/$REPO/releases")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 201 ]; then
    echo "Release created successfully!"
    echo "$BODY" | grep -o '"html_url":"[^"]*"' | cut -d'"' -f4
else
    echo "Error creating release (HTTP $HTTP_CODE):"
    echo "$BODY"
    exit 1
fi


