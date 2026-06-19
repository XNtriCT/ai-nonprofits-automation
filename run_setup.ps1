# AI for Nonprofits — Complete Setup Script
# Run this once to set everything up

Write-Host "=== AI for Nonprofits Setup ===" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# 1. Install Python dependencies
Write-Host "[1/4] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed. Trying with python -m pip..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
}

# 2. Install Playwright Chromium browser
Write-Host "[2/4] Installing Playwright browsers..." -ForegroundColor Yellow
python -m playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Write-Host "Playwright browser install had issues. Trying alternative..." -ForegroundColor Yellow
    python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
}

# 3. Check config
Write-Host "[3/4] Checking configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env" -Destination ".env.template" -ErrorAction SilentlyContinue
    Write-Host ".env not found. Copy from .env.example or create manually." -ForegroundColor Yellow
    Write-Host "  Required: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID" -ForegroundColor Yellow
}

# 4. Test FreeLLMAPI connection
Write-Host "[4/4] Testing FreeLLMAPI connection..." -ForegroundColor Yellow
python -c "
import requests
try:
    r = requests.post('http://172.24.197.38:3001/v1/chat/completions',
        json={'model': 'gpt-4o', 'messages': [{'role': 'user', 'content': 'Say hello'}],
        'max_tokens': 20}, timeout=10)
    print(f'FreeLLMAPI Status: {r.status_code}')
    if r.status_code == 200:
        print(f'Response: {r.json()[\"choices\"][0][\"message\"][\"content\"]}')
    else:
        print(f'Error: {r.text}')
except Exception as e:
    print(f'Cannot reach FreeLLMAPI: {e}')
    print('Make sure FreeLLMAPI router is running on WSL.')
"

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env with your Telegram credentials" -ForegroundColor White
Write-Host "  2. Run:  python main.py --dry-run    # test without image generation" -ForegroundColor White
Write-Host "  3. Run:  python main.py              # full pipeline" -ForegroundColor White
Write-Host "  4. Run:  setup_windows_task.bat      # schedule daily automation" -ForegroundColor White
Write-Host ""
