from django.core.management.base import BaseCommand
from core.models import Prof

class Command(BaseCommand):
    help = 'Deletes all existing professors and creates a new set of predefined professors.'

    def handle(self, *args, **options):
        self.stdout.write("Deleting all existing Prof records...")
        delete_result = Prof.objects.all().delete()
        self.stdout.write(f"Removed {delete_result[0]} professors.")

        self.stdout.write("Creating new professor records...")
        IMG_URL = "https://img.freepik.com/free-photo/portrait-concentrated-young-bearded-man_171337-17191.jpg?semt=ais_hybrid&w=740&q=80"

        items = [
            Prof(
                prof_name="Dr. Eleanor Vance",
                email="evance@university.edu",
                imgurl=IMG_URL,
                description="PhD in Theoretical Physics from MIT. Specializes in quantum field theory and cosmology. Known for her seminal work on dark matter simulations."
            ),
            Prof(
                prof_name="Prof. David Chen",
                email="dchen@university.edu",
                imgurl=IMG_URL,
                description="Masters in Data Science (Stanford). Leads the AI Ethics research group. His field of profession is advanced machine learning and algorithmic fairness."
            ),
            Prof(
                prof_name="Dr. Sofia Martinez",
                email="smartinez@university.edu",
                imgurl=IMG_URL,
                description="Ed.D. in Educational Psychology. Expertise in curriculum development, effective online pedagogy, and K-12 educational technology integration."
            ),
            Prof(
                prof_name="Prof. William O'Connell",
                email="woconnell@university.edu",
                imgurl=IMG_URL,
                description="Juris Doctor (JD) from Yale Law. Field is Constitutional Law and Civil Liberties. He previously served as a litigator for the ACLU."
            ),
            Prof(
                prof_name="Dr. Anya Sharma",
                email="asharma@university.edu",
                imgurl=IMG_URL,
                description="PhD in Organic Chemistry (UC Berkeley). Her research focuses on novel synthesis techniques for pharmaceutical compounds and catalysis."
            ),
            Prof(
                prof_name="Prof. Kenji Tanaka",
                email="ktanaka@university.edu",
                imgurl=IMG_URL,
                description="MBA from Harvard Business School. Professional focus is on corporate finance, risk management, and startup funding strategies."
            ),
            Prof(
                prof_name="Dr. Laura Kim",
                email="lkim@university.edu",
                imgurl=IMG_URL,
                description="PhD in Medieval History (Oxford). Field of profession covers 14th-century European societal structures and the impact of the Black Death."
            ),
            Prof(
                prof_name="Prof. Marcus Bell",
                email="mbell@university.edu",
                imgurl=IMG_URL,
                description="MA in Creative Writing. A published novelist and poet, Prof. Bell teaches advanced fiction workshops and literary analysis."
            ),
            Prof(
                prof_name="Dr. Fatima Hassan",
                email="fhassan@university.edu",
                imgurl=IMG_URL,
                description="PhD in Environmental Engineering. Specialties include water resource management, sustainability practices, and urban infrastructure planning."
            ),
            Prof(
                prof_name="Prof. Jeremy Fiennes",
                email="jfiennes@university.edu",
                imgurl=IMG_URL,
                description="Master of Fine Arts (MFA) in Sculpture. Teaches studio arts, focusing on metalworking and contemporary abstract installation."
            ),
        ]

        # Execute the bulk creation
        Prof.objects.bulk_create(items)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(items)} new professor profiles."))