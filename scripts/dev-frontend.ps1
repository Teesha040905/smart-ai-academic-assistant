cd "$PSScriptRoot\..\frontend"
if (-not (Test-Path .env.local)) {
  "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" | Set-Content .env.local
}
npm run dev
