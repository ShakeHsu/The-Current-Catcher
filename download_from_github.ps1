# GitHub Download Script

# Configuration
$REPO_URL = "https://github.com/ShakeHsu/The-Current-Catcher.git"
$LOCAL_DIR = "C:\Users\XU\Documents\trae_projects\The Current Catcher"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Download Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if directory exists
if (-not (Test-Path $LOCAL_DIR)) {
    Write-Host "Creating directory: $LOCAL_DIR" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $LOCAL_DIR | Out-Null
}

# Change to directory
Set-Location $LOCAL_DIR

# Check if already a Git repository
if (Test-Path ".git") {
    Write-Host "Repository exists, pulling latest code..." -ForegroundColor Green
    git pull origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Code updated to latest version" -ForegroundColor Green
    } else {
        Write-Host "Pull failed, check network connection" -ForegroundColor Red
    }
} else {
    Write-Host "Cloning repository..." -ForegroundColor Yellow
    git clone $REPO_URL
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Repository cloned successfully" -ForegroundColor Green
        Set-Location "The-Current-Catcher"
    } else {
        Write-Host "Clone failed, check network or repo URL" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Show file list
Write-Host "File list:" -ForegroundColor Yellow
Get-ChildItem | Format-Table Name, Length, LastWriteTime

Write-Host ""
Write-Host "Done! You can start working now." -ForegroundColor Green
Write-Host "After modifying code, use these commands to sync:" -ForegroundColor Gray
Write-Host "  git add ." -ForegroundColor Gray
Write-Host "  git commit -m 'description'" -ForegroundColor Gray
Write-Host "  git push" -ForegroundColor Gray