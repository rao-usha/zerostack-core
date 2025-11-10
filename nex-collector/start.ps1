# Load OPENAI_API_KEY from root .env and start services
$env:OPENAI_API_KEY = (Get-Content ..\.env | Select-String -Pattern "^OPENAI_API_KEY=").ToString().Split("=")[1].Trim()
cd nex-collector
docker-compose up -d db redis
Start-Sleep -Seconds 8
docker-compose run --rm api alembic upgrade head
docker-compose up -d api worker

