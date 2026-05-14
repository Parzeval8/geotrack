from django.test import TestCase
from django.contrib.gis.geos import Point
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from .models import Car, WeatherData
from .tasks import fetch_weather
import pybreaker


class GeographicSearchTest(TestCase):
    """
    Tests for the proximity search endpoint.
    Verifies that PostGIS correctly filters cars within a given radius.
    """

    def setUp(self):
        """Create test cars at known locations."""
        self.client = APIClient()

        # Car in Florianópolis — reference point
        self.car_near = Car.objects.create(
            plate='TST1A11',
            brand='Toyota',
            model='Corolla',
            year=2020,
            city='Florianópolis',
            status=Car.Status.WORKING,
            location=Point(-48.5480, -27.5954, srid=4326),
        )

        # Car in Joinville — ~130km from Florianópolis, outside 50km radius
        self.car_far = Car.objects.create(
            plate='TST2B22',
            brand='Honda',
            model='Civic',
            year=2021,
            city='Joinville',
            status=Car.Status.WORKING,
            location=Point(-48.8487, -26.3045, srid=4326),
        )

    def test_nearby_returns_only_cars_within_radius(self):
        """
        Cars outside the radius must not appear in results.
        Florianópolis to Joinville is ~130km — a 50km radius should only return the nearby car.
        """
        response = self.client.get('/api/cars/nearby/', {
            'lat': -27.5954,
            'lon': -48.5480,
            'radius_km': 50,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        plates = [car['plate'] for car in response.data]
        self.assertIn('TST1A11', plates)
        self.assertNotIn('TST2B22', plates)

    def test_nearby_returns_distance_field(self):
        """Results must include the distance_km field."""
        response = self.client.get('/api/cars/nearby/', {
            'lat': -27.5954,
            'lon': -48.5480,
            'radius_km': 50,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertIn('distance_km', response.data[0])

    def test_nearby_requires_all_params(self):
        """Missing parameters must return 400 Bad Request."""
        response = self.client.get('/api/cars/nearby/', {
            'lat': -27.5954,
            # missing lon and radius_km
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_status(self):
        """Filtering by status=working must exclude broken cars."""
        self.car_near.status = Car.Status.BROKEN
        self.car_near.save()

        response = self.client.get('/api/cars/', {'status': 'working'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        plates = [car['plate'] for car in response.data]
        self.assertNotIn('TST1A11', plates)


class WeatherAPIResilienceTest(TestCase):
    """
    Tests for Open-Meteo integration resilience.
    Verifies that the system continues working when the weather API is unavailable.
    """

    def test_fetch_weather_returns_none_on_timeout(self):
        """
        When Open-Meteo times out, fetch_weather must return None
        instead of raising an exception.
        """
        with patch('fleet.tasks.requests.get') as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.Timeout

            result = fetch_weather(-27.5954, -48.5480)
            self.assertIsNone(result)

    def test_fetch_weather_returns_none_on_connection_error(self):
        """
        When Open-Meteo is unreachable, fetch_weather must return None.
        """
        with patch('fleet.tasks.requests.get') as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.ConnectionError

            result = fetch_weather(-27.5954, -48.5480)
            self.assertIsNone(result)

    def test_fetch_weather_returns_none_when_circuit_open(self):
        """
        When the circuit breaker is open (too many failures),
        fetch_weather must return None without attempting the request.
        """
        with patch('fleet.tasks.weather_breaker') as mock_breaker:
            mock_breaker.side_effect = pybreaker.CircuitBreakerError

            result = fetch_weather(-27.5954, -48.5480)
            self.assertIsNone(result)

    def test_fetch_weather_returns_data_on_success(self):
        """
        When Open-Meteo responds correctly, fetch_weather must return
        a dict with temperature, humidity and weather_code.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'current': {
                'temperature_2m': 22.5,
                'relative_humidity_2m': 75,
                'weather_code': 0,
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch('fleet.tasks.requests.get', return_value=mock_response):
            result = fetch_weather(-27.5954, -48.5480)

        self.assertIsNotNone(result)
        self.assertEqual(result['temperature'], 22.5)
        self.assertEqual(result['humidity'], 75)
        self.assertEqual(result['weather_code'], 0)