# Architecture Note

## Context Diagram

The DeployHub system consists of three main components:

1. **Flask Web Service** — handles HTTP requests, serves the UI, calls external services
2. **Supabase PostgreSQL** — stores search history
3. **OpenWeatherMap API** — provides live weather data
```
User → Flask App → OpenWeatherMap API
                 → Supabase PostgreSQL
```

## Integration Points

### OpenWeatherMap API
- Endpoint: `api.openweathermap.org/data/2.5/weather`
- Called on every `/weather` request
- Returns temperature, description, country code, wind, humidity, visibility
- Timeout set to 5 seconds
- Graceful degradation returns 503 if unreachable

### Supabase PostgreSQL
- Hosted managed PostgreSQL instance
- Connected via psycopg3 with SSL required
- Stores city, temperature, description, country code and timestamp per search
- If database is unavailable, weather result is still returned to user

## Branching Model
- Trunk-based development with short-lived feature branches
- All features merged via pull request with at least one review
- Main branch protected — requires passing CI status check before merge
- Branch naming convention: `feature/<description>`

## Pipeline Design
```
Push to main
     ↓
GitHub Actions CI
     ↓
Install dependencies (pip)
     ↓
Build Docker image
     ↓
Push to GHCR (ghcr.io/oisinfc33-sys/deploy-hub:latest)
     ↓
Render auto-deploys from main
     ↓
Live at deploy-hub.onrender.com
```

## Configuration
- 12-factor app style — all secrets via environment variables
- `.env` for local development, GitHub Actions secrets and Render env vars for production
- `.env.example` committed to repo as a template
