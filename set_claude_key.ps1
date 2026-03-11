# PowerShell script to set Claude API key
# Usage: .\set_claude_key.ps1 YOUR_API_KEY_HERE

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiKey
)

Write-Host "🔧 Setting Claude API Key..." -ForegroundColor Green

# Set environment variable for current session
$env:ANTHROPIC_API_KEY = $ApiKey

# Set for future sessions (user level)
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $ApiKey, "User")

Write-Host "✅ Claude API key set for current session" -ForegroundColor Green
Write-Host "✅ Claude API key saved for future PowerShell sessions" -ForegroundColor Green
Write-Host ""
Write-Host "🧪 Testing connection..." -ForegroundColor Yellow

# Test the connection
python setup_claude_key.py
