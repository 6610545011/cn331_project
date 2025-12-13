from django.core.management.base import BaseCommand
from core.models import Prof
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Creates 15 professors with random email, image, and education descriptions.'

    def handle(self, *args, **options):
        self.stdout.write("Deleting all existing Prof records...")
        delete_result = Prof.objects.all().delete()
        self.stdout.write(f"Removed {delete_result[0]} professors.")

        fake = Faker()
        
        IMG_URL = "https://img.freepik.com/free-photo/portrait-concentrated-young-bearded-man_171337-17191.jpg?semt=ais_hybrid&w=740&q=80"
        
        # Education descriptions
        education_descriptions = [
            "PhD in Computer Science from MIT. Specializes in machine learning and artificial intelligence.",
            "Masters in Mathematics from Stanford. Expert in algebraic topology and abstract algebra.",
            "PhD in Physics from Cambridge. Research focus on quantum mechanics and particle physics.",
            "EdD in Education from Harvard. Expertise in curriculum development and pedagogy.",
            "PhD in Chemistry from Berkeley. Specializes in organic synthesis and catalysis.",
            "Masters in Engineering from Princeton. Focus on systems engineering and optimization.",
            "PhD in Biology from Yale. Research in molecular biology and genetics.",
            "Masters in Economics from Oxford. Specializes in macroeconomics and financial markets.",
            "PhD in Literature from Cambridge. Expertise in modern fiction and literary criticism.",
            "Masters in Psychology from MIT. Focus on cognitive psychology and neuroscience.",
            "PhD in Environmental Science from UC Berkeley. Research in climate change and sustainability.",
            "Masters in History from Harvard. Specialization in medieval European history.",
            "PhD in Philosophy from Princeton. Focus on epistemology and metaphysics.",
            "Masters in Statistics from Stanford. Expertise in data analysis and statistical modeling.",
            "PhD in Law from Yale. Specialization in constitutional law and human rights.",
        ]
        
        self.stdout.write("Creating new professor records...")
        
        items = []
        used_emails = set()
        
        for i in range(15):
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            # Generate unique email
            email_base = f"{first_name.lower()}.{last_name.lower()}"
            email = f"{email_base}@university.edu"
            counter = 1
            while email in used_emails:
                email = f"{email_base}{counter}@university.edu"
                counter += 1
            used_emails.add(email)
            
            prof_name = f"Dr. {first_name} {last_name}"
            description = random.choice(education_descriptions)
            
            items.append(Prof(
                prof_name=prof_name,
                email=email,
                imgurl=IMG_URL,
                description=description
            ))
        
        Prof.objects.bulk_create(items)
        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(items)} new professors."))
