from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarViewSet

# DefaultRouter automatically generates URLs for all ViewSet actions
router = DefaultRouter()
router.register(r'cars', CarViewSet, basename='car')

urlpatterns = [
    path('', include(router.urls)),
]