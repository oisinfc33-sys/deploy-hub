# DeployHub — Weather Intelligence

A Flask-based weather web service that integrates OpenWeatherMap and Supabase PostgreSQL, containerised with Docker and deployed via GitHub Actions CI/CD.

## Live Demo
https://deploy-hub.onrender.com

## Tech Stack
- Python 3.11 / Flask
- PostgreSQL (Supabase)
- OpenWeatherMap API
- Docker / GitHub Container Registry
- GitHub Actions CI/CD
- Render (deployment)

## Features
- Live weather search for any city in the world
- Country flags and weather emojis per result
- Temperature-based background colour
- Search history stored in PostgreSQL
- Graceful degradation if database is unavailable

## Endpoints
| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Main UI |
| `/weather?city=Dublin` | GET | Fetch weather for a city |
| `/history` | GET | Last 10 searches from DB |
| `/health` | GET | Health check |
| `/status` | GET | DB and API status |

## Environment Variables
Copy `.env.example` to `.env` and fill in your values:
```
FLASK_APP=app.py
FLASK_ENV=development
WEATHER_API_KEY=your_openweathermap_key
DATABASE_URL=postgresql://user:password@host:5432/postgres?sslmode=require
```

## Run Locally
```bash
git clone https://github.com/oisinfc33-sys/deploy-hub.git
cd deploy-hub
pip install -r requirements.txt
cp .env.example .env
# fill in your .env values
python app.py
```

## Run with Docker
```bash
docker build -t deploy-hub .
docker run -p 5000:5000 --env-file .env deploy-hub
```

## CI/CD Pipeline
- Every push to `main` triggers GitHub Actions
- Pipeline installs dependencies, builds Docker image, pushes to GHCR
- Render auto-deploys from `main` on every push

## Docker Image
```
ghcr.io/oisinfc33-sys/deploy-hub:latest
```
