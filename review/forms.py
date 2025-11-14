from django import forms
from .models import Review, Tag
from core.models import Course, Prof, Section
from .models import Report

class ReviewForm(forms.ModelForm):
    # 1. กำหนด Field ทั้งหมดให้ไม่บังคับเลือก (required=False) ในตอนแรก
    # เราจะใช้เมธอด clean() เพื่อสร้างเงื่อนไขการตรวจสอบที่ซับซ้อนเอง
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(), # จะกำหนด queryset แบบไดนามิกใน __init__
        label="รายวิชา (เลือกจากวิชาที่เคยลงทะเบียน)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_course'})
    )
    
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(), # จะถูกเติมด้วย AJAX
        label="Section (เลือกได้หลังเลือกรายวิชา)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_section'})
    )

    professor = forms.ModelChoiceField(
        queryset=Prof.objects.none(), # จะกำหนด queryset แบบไดนามิกใน __init__
        label="อาจารย์ผู้สอน (เลือกจากอาจารย์ที่เคยเรียนด้วย)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_professor'})
    )

    # ฟิลด์สำหรับเนื้อหารีวิว (ยังคงบังคับกรอก)
    header = forms.CharField(
        label="หัวข้อรีวิว",
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น "วิชานี้ดีมาก เรียนสนุก"'})
    )

    # ฟิลด์สำหรับ Tag (ไม่บังคับเลือก)
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="แท็กที่เกี่ยวข้องกับรีวิวนี้"
    )

    class Meta:
        model = Review
        # ระบุฟิลด์ทั้งหมดที่จะใช้ในฟอร์ม
        fields = ['course', 'section', 'professor', 'header', 'rating', 'body', 'incognito', 'tags']
        
        labels = {
            'body': 'เนื้อหารีวิว',
            'rating': 'ให้คะแนนความพึงพอใจ',
            'incognito': 'ไม่ระบุตัวตน',
        }
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'เล่าประสบการณ์ของคุณเกี่ยวกับวิชานี้...'}),
            'rating': forms.RadioSelect(choices=[(i, str(i)) for i in range(5, 0, -1)]),
            'incognito': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        # 2. รับ 'user' เข้ามาเพื่อใช้กรองข้อมูลใน Dropdown
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # กรอง "รายวิชา" ให้แสดงเฉพาะที่ user เคยลงทะเบียน
            enrolled_courses = Course.objects.filter(
                sections__students=user
            ).distinct().order_by('course_code')
            self.fields['course'].queryset = enrolled_courses

            # กรอง "อาจารย์" ให้แสดงเฉพาะที่เคยสอน user
            taught_professors = Prof.objects.filter(
                teaching_sections__students=user
            ).distinct().order_by('prof_name')
            self.fields['professor'].queryset = taught_professors

        # ทำให้ช่อง Section เริ่มต้นเป็น disabled (จะถูกเปิดใช้งานด้วย JavaScript)
        self.fields['section'].widget.attrs['disabled'] = True

        # จัดการเรื่องชื่อฟิลด์ prof/professor เพื่อให้ ModelForm ทำงานกับ 'prof' ได้ถูกต้อง
        self.fields['professor'].name = 'prof'

    def clean(self):
        # 3. หัวใจของการตรวจสอบ Logic ทั้งหมด
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        section = cleaned_data.get('section')
        prof = cleaned_data.get('prof') # ใช้ 'prof' เพราะเราเปลี่ยนชื่อใน __init__

        # --- Validation 1: ต้องเลือกเป้าหมายรีวิวอย่างน้อย 1 อย่าง ---
        if not course and not prof:
            # Error นี้จะแสดงที่ด้านบนสุดของฟอร์ม (non_field_errors)
            raise forms.ValidationError(
                "กรุณาเลือกอย่างน้อยหนึ่งรายการเพื่อรีวิว (รายวิชา หรือ อาจารย์ผู้สอน)",
                code='no_target'
            )

        # --- Validation 2: ตรวจสอบความสอดคล้องของข้อมูลที่เลือก ---
        # กรณี 2.1: ถ้าเลือก Course และ Section -> Section ต้องอยู่ใน Course นั้น
        if course and section:
            if section.course != course:
                self.add_error('section', f"Section {section.section_number} ไม่ได้อยู่ในรายวิชา {course.course_code}")

        # กรณี 2.2: ถ้าเลือก Course และ Professor -> Professor ต้องเคยสอน Course นั้น
        if course and prof:
            if not Section.objects.filter(course=course, teachers=prof).exists():
                self.add_error('professor', f"{prof.prof_name} ไม่ได้สอนในรายวิชา {course.course_code}")

        # กรณี 2.3: ถ้าเลือก Professor และ Section -> Professor ต้องสอน Section นั้น
        if prof and section:
            if prof not in section.teachers.all():
                self.add_error('professor', f"{prof.prof_name} ไม่ได้สอนใน Section {section.section_number}")

        return cleaned_data

    def save(self, commit=True):
        # 4. จัดการการบันทึกข้อมูลชื่อฟิลด์ที่ไม่ตรงกัน
        instance = super().save(commit=False)
        
        # Map ฟิลด์ 'header' จากฟอร์มไปที่ 'head' ในโมเดล
        instance.head = self.cleaned_data.get('header')
        
        # การ map 'professor' -> 'prof' ถูกจัดการโดย `self.fields['professor'].name = 'prof'` ใน __init__ แล้ว
        # แต่เพื่อความชัดเจน เราสามารถกำหนดค่าอีกครั้งได้
        instance.prof = self.cleaned_data.get('prof')

        if commit:
            instance.save()

        return instance


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please provide a reason for reporting this review...'
            }),
        }
        labels = {
            'comment': 'Reason for reporting',
        }
