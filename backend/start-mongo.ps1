# Start MongoDB locally without requiring Administrator privileges
$mongoExe = "C:\Program Files\MongoDB\Server\8.3\bin\mongod.exe"
$dbPath = Join-Path $PSScriptRoot "data\db"

if (-not (Test-Path $dbPath)) {
    New-Item -ItemType Directory -Force -Path $dbPath | Out-Null
}

Write-Host "Starting MongoDB on localhost:27017 (data path: $dbPath)..." -ForegroundColor Cyan
& $mongoExe --dbpath $dbPath --bind_ip 127.0.0.1 --port 27017
