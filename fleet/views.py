import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django_filters.rest_framework import DjangoFilterBackend
from .models import Car
from .serializers import CarSerializer, CarProximitySerializer

logger = logging.getLogger(__name__)


class CarViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fleet vehicles.
    Provides CRUD operations and geographic proximity search.
    """

    queryset = Car.objects.all().select_related('weather')
    serializer_class = CarSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    @extend_schema(
        summary='List all cars',
        description='Returns all cars in the fleet. Filter by status using ?status=working or ?status=broken.',
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by vehicle status',
                enum=['working', 'broken'],
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Create a car',
        description='Registers a new vehicle in the fleet.',
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Retrieve a car',
        description='Returns a single vehicle by ID.',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Update a car',
        description='Fully updates a vehicle record.',
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Partial update a car',
        description='Partially updates a vehicle record.',
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary='Delete a car',
        description='Removes a vehicle from the fleet.',
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary='Find nearby cars',
        description=(
            'Returns all vehicles within a given radius from a coordinate. '
            'Results are ordered by distance from the reference point.'
        ),
        parameters=[
            OpenApiParameter(
                name='lat',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Latitude of the reference point (e.g. -27.5954)',
                required=True,
            ),
            OpenApiParameter(
                name='lon',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Longitude of the reference point (e.g. -48.5480)',
                required=True,
            ),
            OpenApiParameter(
                name='radius_km',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Search radius in kilometers (e.g. 50)',
                required=True,
            ),
        ],
        responses=CarProximitySerializer(many=True),
    )
    @action(detail=False, methods=['get'], url_path='nearby')
    def nearby(self, request):
        """
        Geographic proximity search using PostGIS ST_DWithin.
        Annotates each result with the distance from the reference point.
        """
        # Validate required query parameters
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius_km = request.query_params.get('radius_km')

        if not all([lat, lon, radius_km]):
            return Response(
                {'error': 'lat, lon and radius_km are required parameters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat = float(lat)
            lon = float(lon)
            radius_km = float(radius_km)
        except ValueError:
            return Response(
                {'error': 'lat, lon and radius_km must be valid numbers.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build reference point from query params
        reference_point = Point(lon, lat, srid=4326)

        # Query cars within radius using PostGIS spatial index
        # D(km=radius_km) creates a Distance object that PostGIS understands
        cars = (
            Car.objects.filter(
                location__dwithin=(reference_point, D(km=radius_km))
            )
            .annotate(distance=Distance('location', reference_point, spherical=True))
            .select_related('weather')
            .order_by('distance')
        )

        logger.info(
            f'Proximity search — ref: ({lat}, {lon}), '
            f'radius: {radius_km}km, results: {cars.count()}'
        )

        serializer = CarProximitySerializer(cars, many=True)
        return Response(serializer.data)