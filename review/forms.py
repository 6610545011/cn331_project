from django import forms
from .models import Review, Tag, Report, ReviewUpvote
from core.models import Course, Prof, Section

class ReviewForm(forms.ModelForm):
    # 1. กำหนด Field ทั้งหมดให้ไม่บังคับเลือก (required=False) ในตอนแรก
    # เราจะใช้เมธอด clean() เพื่อสร้างเงื่อนไขการตรวจสอบที่ซับซ้อนเอง
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(), # filled dynamically in __init__
        label="Course (choose from your registered courses)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_course'})
    )
    
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(), # populated via AJAX
        label="Section (available after selecting a course)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_section'})
    )

    professor = forms.ModelChoiceField(
        queryset=Prof.objects.none(), # filled dynamically in __init__
        label="Professor (choose from instructors you've taken)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_professor'})
    )

    # ฟิลด์สำหรับเนื้อหารีวิว (ยังคงบังคับกรอก)
    header = forms.CharField(
        label="Review title",
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., "This course was great and fun"'})
    )

    # ฟิลด์สำหรับ Tag (ไม่บังคับเลือก)
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Tags for this review"
    )

    class Meta:
        model = Review
        # ระบุฟิลด์ทั้งหมดที่จะใช้ในฟอร์ม
        fields = ['course', 'section', 'prof', 'header', 'rating', 'body', 'incognito', 'tags']
        
        labels = {
            'body': 'Review content',
            'rating': 'Satisfaction rating',
            'incognito': 'Post anonymously',
        }
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Share your experience about this course...'}),
            'rating': forms.RadioSelect(choices=[(i, str(i)) for i in range(5, 0, -1)]),
            'incognito': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        # 2. รับ 'user' เข้ามาเพื่อใช้กรองข้อมูลใน Dropdown
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # keep a reference to user for use in clean()
        self.user = user

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

        # Rename the 'professor' form field to 'prof' so it maps to the model's field name.
        # Keep the HTML id as 'id_professor' so templates/JS continue to work.
        if 'professor' in self.fields:
            prof_field = self.fields.pop('professor')
            self.fields['prof'] = prof_field
            self.fields['prof'].widget.attrs.setdefault('id', 'id_professor')

        # If form is bound (POST), ensure the section queryset includes the submitted choice
        # so ModelChoiceField validation will succeed.
        if self.is_bound:
            # Attempt to read the selected course from submitted data
            course_val = None
            # The key is simply 'course' because field name matches
            if 'course' in self.data:
                course_val = self.data.get('course')
            elif self.initial.get('course'):
                course_val = getattr(self.initial.get('course'), 'id', None)

            if course_val:
                try:
                    course_id = int(course_val)
                    sections_qs = Section.objects.filter(course_id=course_id)
                    # Optionally restrict to sections the user enrolled in
                    if user:
                        sections_qs = sections_qs.filter(students=user)
                    self.fields['section'].queryset = sections_qs.distinct().order_by('section_number')
                    # If a section was submitted, enable the widget so validation runs normally
                    if 'section' in self.data and self.data.get('section'):
                        self.fields['section'].widget.attrs.pop('disabled', None)
                except (TypeError, ValueError):
                    pass

    def clean(self):
        # 3. หัวใจของการตรวจสอบ Logic ทั้งหมด
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        section = cleaned_data.get('section')
        prof = cleaned_data.get('prof') # ใช้ 'prof' เพราะเราเปลี่ยนชื่อใน __init__

        # --- Validation 1: must pick at least one review target ---
        if not course and not prof:
            # Error นี้จะแสดงที่ด้านบนสุดของฟอร์ม (non_field_errors)
            raise forms.ValidationError(
                "Please choose at least one target to review (course or professor)",
                code='no_target'
            )

        # --- Validation 2: ตรวจสอบความสอดคล้องของข้อมูลที่เลือก ---
        # กรณี 2.1: ถ้าเลือก Course และ Section -> Section ต้องอยู่ใน Course นั้น
        if course and section:
            if section.course != course:
                self.add_error('section', f"Section {section.section_number} is not in course {course.course_code}")

        # กรณี 2.2: ถ้าเลือก Course และ Professor -> Professor ต้องเคยสอน Course นั้น
        if course and prof:
            if not Section.objects.filter(course=course, teachers=prof).exists():
                self.add_error('prof', f"{prof.prof_name} does not teach course {course.course_code}")

        # If user selected a professor but no course, try to infer a course.
        # Prefer a course where the user was enrolled with that professor.
        if prof and not course:
            inferred_course = None
            try:
                if hasattr(self, 'user') and self.user:
                    qs = Section.objects.filter(teachers=prof, students=self.user)
                    if qs.exists():
                        inferred_course = qs.first().course
                if not inferred_course:
                    qs_any = Section.objects.filter(teachers=prof)
                    if qs_any.exists():
                        inferred_course = qs_any.first().course
            except Exception:
                inferred_course = None

            if inferred_course:
                cleaned_data['course'] = inferred_course
                course = inferred_course
            else:
                raise forms.ValidationError(
                    "When selecting a professor without a course, no linked course was found — please choose a course or a professor with a course in the system.",
                    code='no_course_for_prof'
                )

        # กรณี 2.3: ถ้าเลือก Professor และ Section -> Professor ต้องสอน Section นั้น
        if prof and section:
            if prof not in section.teachers.all():
                self.add_error('prof', f"{prof.prof_name} does not teach Section {section.section_number}")

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

class ReviewUpvoteForm(forms.ModelForm):
    """
    Form for upvoting or downvoting a review.
    The 'vote_type' is the only field exposed to the user,
    and it will be validated to be either 1 (upvote) or -1 (downvote).
    """
    class Meta:
        model = ReviewUpvote
        fields = ['vote_type']
        widgets = {
            # The vote_type will be submitted via a button, so a hidden input is suitable.
            'vote_type': forms.HiddenInput(),
        }

    def clean_vote_type(self):
        """
        Validate that the vote_type is either 1 or -1.
        """
        vote_type = self.cleaned_data.get('vote_type')
        if vote_type not in [1, -1]:
            raise forms.ValidationError('Invalid vote type. Must be 1 or -1.', code='invalid_vote_type')
        return vote_type
