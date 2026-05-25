@echo off
echo ============================================
echo   aitoolbits-blogger - One-Click Deploy
echo ============================================
echo.
echo Step 1: Creating GitHub repository...
echo   (This requires GitHub CLI or manual creation)
echo.

set REPO_NAME=aitoolbits-blogger
set REPO_DESC=Automated AI blog publisher for aitoolbits.blogspot.com

where gh >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    gh repo create %REPO_NAME% --public --description "%REPO_DESC%" --source=. --push
) else (
    echo GitHub CLI (gh) not found.
    echo.
    echo Please create the repository manually:
    echo   1. Go to https://github.com/new
    echo   2. Repository name: aitoolbits-blogger
    echo   3. Description: Automated AI blog publisher
    echo   4. Make it PUBLIC
    echo   5. Do NOT initialize with README
    echo   6. Click "Create repository"
    echo.
    echo Then run:
    echo   cd /d D:\小程序\aitoolbits-blogger
    echo   git remote add origin https://github.com/iambuluo/aitoolbits-blogger.git
    echo   git push -u origin main
    echo.
    pause
)
