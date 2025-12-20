# PowerShell script to create GitHub release using Personal Access Token
# Usage: .\create_release.ps1 -Token "your_github_token_here"

param(
    [Parameter(Mandatory=$true)]
    [string]$Token
)

$repo = "rendershome/smart_envi"
$tag = "v2.0.0"
$title = "Release v2.0.0 - First Official Release"

# Read release notes
$releaseNotes = Get-Content "RELEASE_NOTES_v2.0.0.md" -Raw

# Create JSON payload
$body = @{
    tag_name = $tag
    name = $title
    body = $releaseNotes
    draft = $false
    prerelease = $false
} | ConvertTo-Json

# Create release via GitHub API
$headers = @{
    "Authorization" = "Bearer $Token"
    "Accept" = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
}

try {
    Write-Host "Creating GitHub release for $tag..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/releases" `
        -Method Post `
        -Headers $headers `
        -Body $body `
        -ContentType "application/json"
    
    Write-Host "Release created successfully!" -ForegroundColor Green
    Write-Host "Release URL: $($response.html_url)" -ForegroundColor Green
    Write-Host "Release ID: $($response.id)" -ForegroundColor Green
} catch {
    Write-Host "Error creating release: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Red
    }
    exit 1
}


