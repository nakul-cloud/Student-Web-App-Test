set dotenv-load := true
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Start the FastAPI backend + served UI : just backend
backend:
    .venv\Scripts\python.exe -m app.server

# Alias for dev server : just dev
dev:
    .venv\Scripts\python.exe -m app.server

# Serve standalone frontend folder on port 3000 (open http://localhost:3000) : just frontend
frontend:
    .venv\Scripts\python.exe -m http.server 3000 --directory frontend

# Start all Docker containers (Postgres, Qdrant, Redis) : just up
up:
    docker compose up -d

# Stop all Docker containers : just down
down:
    docker compose down

# Start & inspect Redis container + active session keys : just redis
redis:
    docker compose up -d redis
    docker exec gift_city_redis redis-cli KEYS "*"

# Start & inspect Qdrant vectorless collection : just qdrant
qdrant:
    docker compose up -d qdrant
    .venv\Scripts\python.exe -c "import httpx; print(httpx.get('http://localhost:6333/collections/gift_city_compliance').json())"

# Start & inspect PostgreSQL users : just postgres
postgres:
    docker compose up -d postgres
    docker exec gift_city_postgres psql -U postgres -d compliance_db -c "SELECT email, full_name, created_at FROM users;"

# Seed / re-seed vectorless Qdrant FAQs : just seed
seed:
    .venv\Scripts\python.exe -c "import asyncio; from app.services.ingestion_service import seed_qdrant_faqs; print('Seeded:', asyncio.run(seed_qdrant_faqs()))"

# Run end-to-end health & API check : just test
test:
    .venv\Scripts\python.exe -c "import httpx; print('Health:', httpx.get('http://localhost:8000/api/v1/chatbot/health').json())"

# Expose live public HTTPS URL for exam submission : just tunnel
tunnel:
    npx localtunnel --port 8000
