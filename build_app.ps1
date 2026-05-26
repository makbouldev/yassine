$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt pyinstaller

python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name YassineExcelManager `
    --collect-all customtkinter `
    --collect-all tksheet `
    --collect-all psycopg `
    --hidden-import psycopg_binary `
    main.py

$appDir = Join-Path $PSScriptRoot "dist\YassineExcelManager"

if (Test-Path (Join-Path $PSScriptRoot ".env")) {
    Copy-Item -Path (Join-Path $PSScriptRoot ".env") -Destination (Join-Path $appDir ".env") -Force
}

if (Test-Path (Join-Path $PSScriptRoot "default_table.xlsx")) {
    Copy-Item -Path (Join-Path $PSScriptRoot "default_table.xlsx") -Destination (Join-Path $appDir "default_table.xlsx") -Force
}

$shareReadme = @"
Yassine Excel Manager

Run:
1. Open this folder.
2. Double-click YassineExcelManager.exe.

Important:
- Keep .env in the same folder as YassineExcelManager.exe.
- .env connects the app to the shared online database.
- Do not upload or share .env publicly.
"@

Set-Content -Path (Join-Path $appDir "README_SHARE.txt") -Value $shareReadme -Encoding UTF8

$zipPath = Join-Path $PSScriptRoot "dist\YassineExcelManager.zip"
if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}
Compress-Archive -Path (Join-Path $appDir "*") -DestinationPath $zipPath -Force

Write-Output "Build complete:"
Write-Output $appDir
Write-Output $zipPath
