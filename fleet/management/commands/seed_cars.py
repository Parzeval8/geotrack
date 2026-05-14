from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from fleet.models import Car


# Real cities in Santa Catarina with accurate GPS coordinates
CARS_DATA = [
    {
        'city': 'Florianópolis',
        'latitude': -27.5954,
        'longitude': -48.5480,
        'plate': 'ABC1D23',
        'brand': 'Volkswagen',
        'model': 'Gol',
        'year': 2019,
    },
    {
        'city': 'Joinville',
        'latitude': -26.3045,
        'longitude': -48.8487,
        'plate': 'BCD2E34',
        'brand': 'Fiat',
        'model': 'Uno',
        'year': 2020,
    },
    {
        'city': 'Blumenau',
        'latitude': -26.9194,
        'longitude': -49.0661,
        'plate': 'CDE3F45',
        'brand': 'Chevrolet',
        'model': 'Onix',
        'year': 2021,
    },
    {
        'city': 'São José',
        'latitude': -27.5939,
        'longitude': -48.6353,
        'plate': 'DEF4G56',
        'brand': 'Ford',
        'model': 'Ka',
        'year': 2018,
    },
    {
        'city': 'Criciúma',
        'latitude': -28.6773,
        'longitude': -49.3701,
        'plate': 'EFG5H67',
        'brand': 'Hyundai',
        'model': 'HB20',
        'year': 2022,
    },
    {
        'city': 'Chapecó',
        'latitude': -27.1004,
        'longitude': -52.6152,
        'plate': 'FGH6I78',
        'brand': 'Renault',
        'model': 'Kwid',
        'year': 2021,
    },
    {
        'city': 'Itajaí',
        'latitude': -26.9078,
        'longitude': -48.6619,
        'plate': 'GHI7J89',
        'brand': 'Toyota',
        'model': 'Corolla',
        'year': 2020,
    },
    {
        'city': 'Lages',
        'latitude': -27.8150,
        'longitude': -50.3267,
        'plate': 'HIJ8K90',
        'brand': 'Honda',
        'model': 'Civic',
        'year': 2019,
    },
    {
        'city': 'Jaraguá do Sul',
        'latitude': -26.4853,
        'longitude': -49.0650,
        'plate': 'IJK9L01',
        'brand': 'Nissan',
        'model': 'Versa',
        'year': 2022,
    },
    {
        'city': 'Palhoça',
        'latitude': -27.6453,
        'longitude': -48.6695,
        'plate': 'JKL0M12',
        'brand': 'Volkswagen',
        'model': 'Polo',
        'year': 2021,
    },
    {
        'city': 'Balneário Camboriú',
        'latitude': -26.9906,
        'longitude': -48.6348,
        'plate': 'KLM1N23',
        'brand': 'Fiat',
        'model': 'Argo',
        'year': 2022,
    },
    {
        'city': 'Brusque',
        'latitude': -27.0983,
        'longitude': -48.9156,
        'plate': 'LMN2O34',
        'brand': 'Chevrolet',
        'model': 'Tracker',
        'year': 2020,
    },
    {
        'city': 'Tubarão',
        'latitude': -28.4667,
        'longitude': -49.0033,
        'plate': 'MNO3P45',
        'brand': 'Ford',
        'model': 'EcoSport',
        'year': 2019,
    },
    {
        'city': 'São Bento do Sul',
        'latitude': -26.2500,
        'longitude': -49.3833,
        'plate': 'NOP4Q56',
        'brand': 'Toyota',
        'model': 'Hilux',
        'year': 2021,
    },
    {
        'city': 'Caçador',
        'latitude': -26.7753,
        'longitude': -51.0144,
        'plate': 'OPQ5R67',
        'brand': 'Renault',
        'model': 'Duster',
        'year': 2020,
    },
    {
        'city': 'Concórdia',
        'latitude': -27.2344,
        'longitude': -52.0272,
        'plate': 'PQR6S78',
        'brand': 'Honda',
        'model': 'HR-V',
        'year': 2022,
    },
    {
        'city': 'Araranguá',
        'latitude': -28.9342,
        'longitude': -49.4811,
        'plate': 'QRS7T89',
        'brand': 'Jeep',
        'model': 'Renegade',
        'year': 2021,
    },
    {
        'city': 'Navegantes',
        'latitude': -26.8986,
        'longitude': -48.6553,
        'plate': 'RST8U90',
        'brand': 'Nissan',
        'model': 'Kicks',
        'year': 2020,
    },
    {
        'city': 'Camboriú',
        'latitude': -27.0236,
        'longitude': -48.6539,
        'plate': 'STU9V01',
        'brand': 'Hyundai',
        'model': 'Creta',
        'year': 2022,
    },
    {
        'city': 'Içara',
        'latitude': -28.7133,
        'longitude': -49.3044,
        'plate': 'TUV0W12',
        'brand': 'Volkswagen',
        'model': 'T-Cross',
        'year': 2021,
    },
]


class Command(BaseCommand):
    help = 'Seeds the database with 20 cars distributed across Santa Catarina cities'

    def handle(self, *args, **kwargs):
        # Skip seeding if cars already exist to avoid duplicates on container restart
        if Car.objects.exists():
            self.stdout.write(self.style.WARNING('Database already seeded — skipping.'))
            return

        cars_created = 0

        for data in CARS_DATA:
            Car.objects.create(
                plate=data['plate'],
                brand=data['brand'],
                model=data['model'],
                year=data['year'],
                city=data['city'],
                # Point takes (longitude, latitude)
                location=Point(data['longitude'], data['latitude'], srid=4326),
            )
            cars_created += 1
            self.stdout.write(f"  ✓ {data['plate']} — {data['brand']} {data['model']} in {data['city']}")

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully seeded {cars_created} cars across Santa Catarina.')
        )