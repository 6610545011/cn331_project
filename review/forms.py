from django import forms
from .models import Review, Course, Professor

class ReviewForm(forms.ModelForm):
    # กำหนดให้ rating เป็น RadioSelect เพื่อให้เลือกดาวได้ง่ายขึ้น
    rating = forms.ChoiceField(
        choices=[(i, f'{i} ดาว') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'rating-choices'}),
        label="ให้คะแนน"
    )

    class Meta:
        model = Review
        # เลือกฟิลด์ที่จะแสดงในฟอร์ม
        fields = ['course', 'professor', 'rating', 'header', 'body', 'incognito']
        
        labels = {
            'course': 'รายวิชา',
            'professor': 'อาจารย์ผู้สอน',
            'header': 'หัวข้อรีวิว',
            'body': 'เนื้อหารีวิว',
            'incognito': 'ไม่แสดงตัวตน (Incognito)',
        }

        widgets = {
            'course': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'เลือกรหัสวิชาหรือชื่อวิชา'
            }),
            'professor': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'เลือกอาจารย์ผู้สอน'
            }),
            'header': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'เช่น "วิชานี้ดีมาก เรียนสนุก ได้ความรู้เต็มๆ"'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'อธิบายรายละเอียดเพิ่มเติมเกี่ยวกับการเรียนการสอน การบ้าน โปรเจกต์ และการสอบ...'
            }),
            'incognito': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ทำให้ dropdown แสดงข้อความเริ่มต้น
        # self.fields['course'].empty_label = "--- เลือกรหัสวิชา ---"
        # self.fields['professor'].empty_label = "--- เลือกอาจารย์ผู้สอน ---"
        # ควบคุมข้อความเริ่มต้นด้วย JavaScript/Select2 แทน