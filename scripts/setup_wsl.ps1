# ============================================
# Sovereign AI Workbench — WSL2 Setup Script
# ============================================
# Run in PowerShell as Administrator

Write-Host "🛡️  Sovereign AI Workbench — WSL2 Setup" -ForegroundColor Cyan

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Please run as Administrator" -ForegroundColor Red
    exit 1
}

# Enable WSL
Write-Host "`n[1/4] Enabling WSL..." -ForegroundColor Yellow
wsl --install --no-distribution

# Set WSL2 as default
Write-Host "`n[2/4] Setting WSL2 as default..." -ForegroundColor Yellow
wsl --set-default-version 2

# Update WSL
Write-Host "`n[3/4] Updating WSL..." -ForegroundColor Yellow
wsl --update

# Install Ubuntu
Write-Host "`n[4/4] Installing Ubuntu..." -ForegroundColor Yellow
wsl --install -d Ubuntu

Write-Host "`n✅ WSL2 setup complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Restart your computer" -ForegroundColor White
Write-Host "  2. Open Ubuntu from Start menu to complete setup" -ForegroundColor White
Write-Host "  3. Run scripts/setup_ubuntu.sh inside Ubuntu" -ForegroundColor White
