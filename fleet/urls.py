from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarViewSet, map_view

router = DefaultRouter()
router.register(r'cars', CarViewSet, basename='car')

urlpatterns = [
    path('', include(router.urls)),
    # Fleet dashboard with Leaflet map
    path('map/', map_view, name='fleet-map'),
]