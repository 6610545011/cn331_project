from django.core.management.base import BaseCommand
from core.models import Campus
import random

class Command(BaseCommand):
    help = 'Creates 4 random cities as campuses in the database.'

    def handle(self, *args, **options):
        self.stdout.write("Deleting all existing Campus records...")
        delete_result = Campus.objects.all().delete()
        self.stdout.write(f"Removed {delete_result[0]} campuses.")

        # List of cities from different countries
        cities = [
            "Bangkok", "Chiang Mai", "Phuket", "Krabi", "Ayutthaya",
            "Pattaya", "Khon Kaen", "Udon Thani", "Nakhon Ratchasima", "Chachoengsao",
            "Rayong", "Trat", "Amnat Charoen", "Nong Bua Lam Phu", "Roi Et",
            "Kalasin", "Yasothon", "Amnat Charoen", "Sa Kaeo", "Chaiyaphum",
            "Prachuap Khiri Khan", "Samut Prakan", "Samut Sakhon", "Samut Songkhram", "Nakhon Pathom"
        ]
        
        # Pick 4 random unique cities
        selected_cities = random.sample(cities, 4)
        
        self.stdout.write(f"Creating new campus records with cities: {selected_cities}")
        items = [Campus(name=city) for city in selected_cities]
        
        Campus.objects.bulk_create(items)
        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(items)} new campuses."))
