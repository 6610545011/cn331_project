from django import forms
from .models import Review, Course, Professor, Section # <-- เพิ่ม Section

class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)], # เปลี่ยน label เป็นแค่ตัวเลข
        widget=forms.RadioSelect(), # ไม่ต้องใช้ class แล้ว เพราะเราจะซ่อนมัน
        label="ให้คะแนน"
    )

    class Meta:
        model = Review
        # --- เพิ่ม 'section' เข้าไปใน fields ---
        fields = ['course', 'section', 'professor', 'rating', 'header', 'body', 'incognito']
        
        labels = {
            'course': 'รายวิชา',
            'section': 'กลุ่มเรียน (Section)', # <-- เพิ่ม label
            'professor': 'อาจารย์ผู้สอน',
            'header': 'หัวข้อรีวิว',
            'body': 'เนื้อหารีวิว',
            'incognito': 'ไม่แสดงตัวตน (Incognito)',
        }

        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            # --- เพิ่ม widget สำหรับ section ---
            'section': forms.Select(attrs={'class': 'form-control'}),
            'professor': forms.Select(attrs={'class': 'form-control'}),
            'header': forms.TextInput(attrs={
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
        # --- เพิ่มข้อความเริ่มต้นสำหรับ section และ professor ---
        self.fields['section'].choices = [("", "--- กรุณาเลือกรายวิชาก่อน ---")]
        self.fields['professor'].choices = [("", "--- กรุณาเลือกรายวิชาก่อน ---")]