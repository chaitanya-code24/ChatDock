$ErrorActionPreference = "Stop"

Set-Location "$PSScriptRoot\\..\\backend"
..\\backend\\venv\\Scripts\\python.exe -m alembic -c alembic.ini upgrade head
Write-Output "Migration complete."

