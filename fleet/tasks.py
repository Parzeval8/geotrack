import logging
import random
import requests
import pybreaker
from celery import shared_task
from django.conf import settings
from django.contrib.gis.geos import Point
from .models import Car, WeatherData

logger = logging.getLogger(__name__)

# Circuit breaker for Open-Meteo API
# Opens after 3 consecutive failures, resets after 60 seconds
weather_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=60,
    name='open_meteo',
)

# Maximum distance a car can move per simulation cycle (in degrees)
# ~0.01 degrees ≈ 1km
MAX_MOVEMENT = 0.01


def fetch_weather(lat: float, lon: float) -> dict | None:
    """
    Fetches current weather from Open-Meteo API.
    Protected by a circuit breaker to prevent cascade failures.
    Returns None if the API is unavailable or circuit is open.
    """
    url = (
        f'https://api.open-meteo.com/v1/forecast'
        f'?latitude={lat}&longitude={lon}'
        f'&current=temperature_2m,relative_humidity_2m,weather_code'
        f'&timezone=auto'
    )

    try:
        # Circuit breaker wraps the HTTP call
        # If it fails 3 times, it stops calling for 60 seconds
        @weather_breaker
        def call_api():
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()

        data = call_api()
        current = data.get('current', {})

        return {
            'temperature': current.get('temperature_2m'),
            'humidity': current.get('relative_humidity_2m'),
            'weather_code': current.get('weather_code'),
        }

    except pybreaker.CircuitBreakerError:
        logger.warning('open_meteo circuit breaker is open — skipping weather fetch')
        return None

    except requests.exceptions.Timeout:
        logger.error('open_meteo request timed out')
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f'open_meteo request failed: {e}')
        return None

    except Exception as e:
        logger.error(f'unexpected error fetching weather: {e}')
        return None


def simulate_movement(car: Car) -> Point:
    """
    Simulates vehicle movement by applying a small random offset
    to the current position. Movement is bounded to stay within
    a realistic range around Santa Catarina.
    """
    current_lat = car.location.y
    current_lon = car.location.x

    # Apply random offset within MAX_MOVEMENT range
    new_lat = current_lat + random.uniform(-MAX_MOVEMENT, MAX_MOVEMENT)
    new_lon = current_lon + random.uniform(-MAX_MOVEMENT, MAX_MOVEMENT)

    # Keep coordinates within Santa Catarina bounding box
    new_lat = max(-30.0, min(-25.9, new_lat))
    new_lon = max(-54.0, min(-48.3, new_lon))

    return Point(new_lon, new_lat, srid=4326)


@shared_task(bind=True, max_retries=3)
def simulate_fleet(self):
    """
    Periodic task that runs every SIMULATION_INTERVAL_SECONDS.
    For each car:
      1. Updates position (simulates movement)
      2. Randomly updates operational status
      3. Fetches weather for the new position
    """
    logger.info('--- simulation cycle started ---')

    cars = Car.objects.all()
    total = cars.count()
    success_count = 0
    error_count = 0

    for car in cars:
        try:
            # 1. Simulate movement
            car.location = simulate_movement(car)

            # 2. Randomly toggle status — 20% chance of changing state
            if random.random() < 0.2:
                car.status = (
                    Car.Status.BROKEN
                    if car.status == Car.Status.WORKING
                    else Car.Status.WORKING
                )

            car.save()

            # 3. Fetch weather for new position
            weather_data = fetch_weather(car.location.y, car.location.x)

            if weather_data:
                # update_or_create — updates if exists, creates if not
                WeatherData.objects.update_or_create(
                    car=car,
                    defaults=weather_data,
                )
                logger.info(
                    f'[OK] {car.plate} — '
                    f'pos: ({car.location.y:.4f}, {car.location.x:.4f}) '
                    f'status: {car.status} '
                    f'temp: {weather_data["temperature"]}°C'
                )
            else:
                logger.info(
                    f'[OK] {car.plate} — '
                    f'pos: ({car.location.y:.4f}, {car.location.x:.4f}) '
                    f'status: {car.status} '
                    f'(weather unavailable)'
                )

            success_count += 1

        except Exception as e:
            error_count += 1
            logger.error(f'[ERROR] failed to update car {car.plate}: {e}')

    logger.info(
        f'--- simulation cycle finished — '
        f'{success_count}/{total} updated, {error_count} errors ---'
    )