# review/forms.py

from django import forms
from .models import Review
from core.models import Course, Prof, Section
from .models import Report

class ReviewForm(forms.ModelForm):
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        label="รายวิชา",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_course'})
    )
    
    # --- แก้ไขตรงนี้ ---
    # เปลี่ยนจาก CharField เป็น ModelChoiceField
    # เราจะใช้ JavaScript เพื่อเติมตัวเลือกเข้ามาทีหลัง
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(), # เริ่มต้นให้เป็นค่าว่าง
        label="Section",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_section'})
    )

    professor = forms.ModelChoiceField(
        queryset=Prof.objects.none(),
        label="อาจารย์ผู้สอน",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_professor'})
    )

    header = forms.CharField(
        label="หัวข้อรีวิว",
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น "วิชานี้ดีมาก เรียนสนุก"'})
    )

    class Meta:
        model = Review
        # --- แก้ไขตรงนี้ ---
        # เปลี่ยน 'section_number' เป็น 'section'
        fields = ['course', 'section', 'professor', 'rating', 'header', 'body', 'incognito']
        
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
        super().__init__(*args, **kwargs)
        self.fields['professor'].queryset = Prof.objects.all()
        self.fields['professor'].to_field_name = 'id'
        self.fields['professor'].label_from_instance = lambda obj: obj.prof_name
        self.fields['professor'].name = 'prof'

    # --- แก้ไขตรงนี้ ---
    # เราไม่ต้องการ clean() แบบเดิมแล้ว เพราะ ModelChoiceField จัดการการตรวจสอบให้เรา
    # สามารถลบเมธอด clean() ทิ้งไปได้เลย หรือจะเหลือไว้เผื่อ validation อื่นๆ ในอนาคตก็ได้
    def clean(self):
        cleaned_data = super().clean()
        # ไม่ต้องมี logic การค้นหา section แล้ว
        return cleaned_data

    # --- แก้ไขตรงนี้ ---
    # เราสามารถทำให้เมธอด save() ง่ายลงได้
    # เพราะชื่อฟิลด์ 'section' ในฟอร์มตรงกับในโมเดลแล้ว ModelForm จะจัดการให้เอง
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # ไม่ต้องกำหนด instance.section เองแล้ว
        instance.head = self.cleaned_data.get('header')
        instance.prof = self.cleaned_data.get('professor')

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