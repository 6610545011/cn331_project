import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cn331_project.settings')
django.setup()

from core.models import Section, SectionTime

sections = Section.objects.all()
print(f'Total sections: {sections.count()}')

for sec in sections[:3]:
    times = SectionTime.objects.filter(section=sec)
    print(f'\nSection {sec.id} ({sec.course.course_code} - {sec.section_number}):', end=' ')
    print(f'{times.count()} time slots linked')
    for st in times:
        print(f'  - {st.slot.time}')
