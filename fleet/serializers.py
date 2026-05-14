from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import Car, WeatherData


class WeatherDataSerializer(serializers.ModelSerializer):
    """Serializes the latest weather reading associated with a car."""

    class Meta:
        model = WeatherData
        fields = ['temperature', 'humidity', 'weather_code', 'recorded_at']


class CarSerializer(serializers.ModelSerializer):
    """
    Main serializer for Car model.
    Exposes latitude/longitude as separate fields instead of raw GeoJSON
    to keep the API response simple and frontend-friendly.
    """

    # Read-only fields derived from the PointField
    latitude = serializers.FloatField(read_only=True)
    longitude = serializers.FloatField(read_only=True)

    # Nested weather data — read only, updated by simulation task
    weather = WeatherDataSerializer(read_only=True)

    # Write-only fields — used to create/update the PointField
    # These are not stored directly, they build the Point object
    lat = serializers.FloatField(write_only=True, required=True)
    lon = serializers.FloatField(write_only=True, required=True)

    class Meta:
        model = Car
        fields = [
            'id',
            'plate',
            'brand',
            'model',
            'year',
            'status',
            'city',
            'latitude',   # read-only — from PointField
            'longitude',  # read-only — from PointField
            'lat',        # write-only — to create/update PointField
            'lon',        # write-only — to create/update PointField
            'weather',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_year(self, value):
        """Ensure the year is reasonable."""
        if value < 1900 or value > 2100:
            raise serializers.ValidationError('Year must be between 1900 and 2100.')
        return value

    def validate_lat(self, value):
        """Latitude must be within valid geographic bounds."""
        if value < -90 or value > 90:
            raise serializers.ValidationError('Latitude must be between -90 and 90.')
        return value

    def validate_lon(self, value):
        """Longitude must be within valid geographic bounds."""
        if value < -180 or value > 180:
            raise serializers.ValidationError('Longitude must be between -180 and 180.')
        return value

    def create(self, validated_data):
        # Extract lat/lon and build the PostGIS Point before saving
        lat = validated_data.pop('lat')
        lon = validated_data.pop('lon')
        validated_data['location'] = Point(lon, lat, srid=4326)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Update location only if new coordinates are provided
        lat = validated_data.pop('lat', None)
        lon = validated_data.pop('lon', None)
        if lat is not None and lon is not None:
            validated_data['location'] = Point(lon, lat, srid=4326)
        return super().update(instance, validated_data)


class CarProximitySerializer(CarSerializer):
    """
    Extends CarSerializer with distance information.
    Used exclusively in the proximity search endpoint.
    """

    # Distance in kilometers — annotated by the PostGIS query
    distance_km = serializers.SerializerMethodField()

    class Meta(CarSerializer.Meta):
        fields = CarSerializer.Meta.fields + ['distance_km']

    def get_distance_km(self, obj):
        """Return distance rounded to 2 decimal places if available."""
        if hasattr(obj, 'distance'):
            return round(obj.distance.km, 2)
        return None