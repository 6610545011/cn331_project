from django.core.management.base import BaseCommand
from core.models import Section, SectionTime

class Command(BaseCommand):
    def handle(self, *args, **options):
        sections = Section.objects.all()
        self.stdout.write(f"Total sections: {sections.count()}")
        
        for sec in sections[:5]:
            times = SectionTime.objects.filter(section=sec)
            self.stdout.write(f"\nSection {sec.id} ({sec.course.course_code} - {sec.section_number}): {times.count()} time slots linked")
            for st in times:
                self.stdout.write(f"  - {st.slot.time}")
