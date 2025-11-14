from django import forms
from django.core.exceptions import ValidationError # <-- เพิ่ม import นี้
from .models import Review, Course, Prof, Section

class ReviewForm(forms.ModelForm):
    # --- เปลี่ยนฟิลด์ section ตรงนี้ ---
    # เราจะ override ฟิลด์ section ให้เป็น CharField เพื่อรับข้อความ
    section = forms.CharField(
        label="กลุ่มเรียน (Section)",
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น 701, 731'})
    )

    rating = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect(),
        label="ให้คะแนน"
    )

    class Meta:
        model = Review
        # เอา 'section' ออกจาก fields นี้ เพราะเรา override ไปแล้ว
        fields = ['course', 'prof', 'rating', 'head', 'body', 'incognito']
        
        labels = {
            'course': 'รายวิชา',
            'prof': 'อาจารย์ผู้สอน',
            'head': 'หัวข้อรีวิว',
            'body': 'เนื้อหารีวิว',
            'incognito': 'ไม่แสดงตัวตน (Incognito)',
        }
        # ... widgets อื่นๆ เหมือนเดิม ...
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'prof': forms.Select(attrs={'class': 'form-control'}),
            'head': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'เช่น "วิชานี้ดีมาก เรียนสนุก ได้ความรู้เต็มๆ"'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'อธิบายรายละเอียดเพิ่มเติม...'
            }),
            'incognito': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ไม่ต้องตั้งค่า choices ให้ section แล้ว
        self.fields['prof'].choices = [("", "--- กรุณาเลือกรายวิชาก่อน ---")]

    # --- เพิ่มเมธอด clean() เพื่อแปลง section number เป็น object ---
    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get("course")
        section_number_str = cleaned_data.get("section")

        if course and section_number_str:
            try:
                # ค้นหา Section object จาก course และ section number ที่ผู้ใช้กรอก
                section_obj = Section.objects.get(course=course, section_number=section_number_str)
                # แทนที่ string ใน cleaned_data ด้วย object ที่เราหาเจอ
                cleaned_data['section'] = section_obj
            except Section.DoesNotExist:
                # ถ้าหาไม่เจอ ให้สร้าง validation error
                raise ValidationError(
                    f"ไม่พบ Section '{section_number_str}' สำหรับรายวิชา {course.code}."
                )
        
        return cleaned_data

    # --- แก้ไขเมธอด save() เพื่อให้ทำงานกับฟิลด์ที่เรา override ---
    def save(self, commit=True):
        # ตั้งค่า instance.section จาก cleaned_data ที่เราแปลงเป็น object แล้ว
        self.instance.section = self.cleaned_data.get('section')
        return super().save(commit=commit)