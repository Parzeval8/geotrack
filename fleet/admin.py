from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import Car, WeatherData


@admin.register(Car)
class CarAdmin(GISModelAdmin):
    """
    Admin interface for Car model.
    GISModelAdmin renders an interactive map for the PointField.
    """
    list_display = ['plate', 'brand', 'model', 'year', 'city', 'status', 'updated_at']
    list_filter = ['status', 'brand']
    search_fields = ['plate', 'city', 'brand', 'model']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['car', 'temperature', 'humidity', 'weather_code', 'recorded_at']
    readonly_fields = ['recorded_at']