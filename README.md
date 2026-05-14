# GeoTrack 🛰

Fleet tracking system with geographic data and real-time weather integration.
Built with Django, PostGIS, Celery, and Redis.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 + Django REST Framework |
| Database | PostgreSQL 15 + PostGIS 3.3 |
| Background Tasks | Celery + Redis |
| Geographic Queries | GeoDjango + PostGIS (ST_DWithin) |
| Weather API | Open-Meteo (free, no auth required) |
| API Docs | drf-spectacular (Swagger UI) |
| Frontend | Leaflet.js + Bootstrap 5 |
| Infrastructure | Docker + Docker Compose |

---

## Architecture Decisions

### Why PostGIS?
PostGIS extends PostgreSQL with geographic data types and spatial functions.
The `PointField(geography=True)` stores vehicle coordinates as geographic points,
enabling efficient radius queries using `ST_DWithin` with meter-based units.

### Why Celery + Redis?
The simulation task runs every `SIMULATION_INTERVAL_SECONDS` seconds in background,
updating vehicle positions and fetching weather data without blocking the API.
Celery Beat acts as the scheduler, storing periodic task configuration in the database.
Redis serves as the message broker between Beat and the Worker.

### Why Circuit Breaker?
The Open-Meteo integration uses `pybreaker` to implement a circuit breaker pattern.
After 3 consecutive failures, the breaker opens and stops calling the API for 60 seconds,
preventing cascade failures and reducing unnecessary network traffic.

### Data Model
- **Car** — vehicle entity with plate, brand, model, year, status, and PostGIS PointField
- **WeatherData** — one-to-one with Car, stores only the latest weather reading per vehicle

---

## Requirements

- Docker
- Docker Compose

---

## Setup & Running

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/geotrack.git
cd geotrack
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

### 3. Start all services

```bash
docker compose up --build
```

This single command will:
- Start PostgreSQL with PostGIS
- Start Redis
- Run Django migrations
- Seed the database with 20 cars across Santa Catarina
- Start the Django API server
- Start the Celery worker
- Start the Celery Beat scheduler

### 4. Access the application

| Service | URL |
|---------|-----|
| Fleet Dashboard | http://localhost:8000/ |
| Swagger UI | http://localhost:8000/api/docs/ |
| Django Admin | http://localhost:8000/admin/ |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Django debug mode | `True` |
| `SECRET_KEY` | Django secret key | — |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `DB_NAME` | PostgreSQL database name | `geotrack` |
| `DB_USER` | PostgreSQL user | `geotrack` |
| `DB_PASSWORD` | PostgreSQL password | `geotrack` |
| `DB_HOST` | PostgreSQL host | `db` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `SIMULATION_INTERVAL_SECONDS` | How often vehicles are updated | `30` |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/cars/` | List all vehicles |
| `POST` | `/api/cars/` | Register a new vehicle |
| `GET` | `/api/cars/{id}/` | Retrieve a vehicle |
| `PUT` | `/api/cars/{id}/` | Update a vehicle |
| `PATCH` | `/api/cars/{id}/` | Partial update |
| `DELETE` | `/api/cars/{id}/` | Remove a vehicle |
| `GET` | `/api/cars/?status=working` | Filter by status |
| `GET` | `/api/cars/nearby/` | Proximity search |

### Proximity Search Example

```
GET /api/cars/nearby/?lat=-27.5954&lon=-48.5480&radius_km=50
```

Returns all vehicles within 50km of Florianópolis, ordered by distance.

---

## Running Tests

```bash
docker compose exec web python manage.py test fleet --verbosity=2
```

Expected output: **8 tests passing**

---

## What Was Not Implemented

| Feature | Reason |
|---------|--------|
| CRUD frontend | Given the project priorities and development timeline, this was the most dispensable optional feature. The core requirements — PostGIS geographic queries, Celery background simulation, Open-Meteo integration with circuit breaker, automated tests, and the Leaflet dashboard — were prioritized instead. Swagger UI covers this requirement completely and is explicitly accepted as the primary demonstration interface in the challenge specification. |

---

## Project Structure

```
geotrack/
├── docker-compose.yml        # All services definition
├── Dockerfile                # Application image
├── entrypoint.sh             # Web service startup (migrations + seed + server)
├── entrypoint-worker.sh      # Celery worker startup
├── entrypoint-beat.sh        # Celery beat startup (waits for migrations)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── geotrack/
│   ├── settings.py           # Django configuration
│   ├── urls.py               # Root URL routing
│   └── celery.py             # Celery application instance
└── fleet/
    ├── models.py             # Car and WeatherData models
    ├── serializers.py        # API serializers
    ├── views.py              # API views and proximity search
    ├── urls.py               # Fleet URL routing
    ├── tasks.py              # Simulation and weather tasks
    ├── admin.py              # Django admin configuration
    ├── tests.py              # Automated tests
    ├── templates/
    │   └── fleet/
    │       └── map.html      # Leaflet dashboard
    └── management/
        └── commands/
            └── seed_cars.py  # Database seeding command
```