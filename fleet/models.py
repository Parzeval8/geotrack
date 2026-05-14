from django.contrib.gis.db import models
from django.contrib.gis.geos import Point


class Car(models.Model):
    """
    Represents a vehicle in the fleet.
    Uses PointField (PostGIS) to store geographic coordinates.
    """

    class Status(models.TextChoices):
        WORKING = 'working', 'Working'
        BROKEN = 'broken', 'Broken'

    # Vehicle identification
    plate = models.CharField(max_length=10, unique=True)
    model = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    year = models.IntegerField()

    # Operational status — randomly updated by the simulation task
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.WORKING,
    )

    # Geographic position stored as a PostGIS point (longitude, latitude)
    # srid=4326 is the standard GPS coordinate system (WGS84)
    location = models.PointField(srid=4326)

    # City name for human-readable reference
    city = models.CharField(max_length=100)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['plate']

    def __str__(self):
        return f'{self.plate} — {self.brand} {self.model} ({self.city})'

    @property
    def latitude(self):
        return self.location.y

    @property
    def longitude(self):
        return self.location.x


class WeatherData(models.Model):
    """
    Stores the latest weather forecast for a vehicle's current location.
    One-to-one relationship with Car — only the most recent reading is kept.
    """

    # One weather record per car — updated on each simulation cycle
    car = models.OneToOneField(
        Car,
        on_delete=models.CASCADE,
        related_name='weather'
    )

    temperature = models.FloatField()
    humidity = models.IntegerField()

    # WMO weather code — integer that represents weather condition
    weather_code = models.IntegerField()

    # Timestamp of the last successful API call
    recorded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Weather for {self.car.plate} — {self.temperature}°C'