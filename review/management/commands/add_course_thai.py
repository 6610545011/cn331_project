from django.core.management.base import BaseCommand
from core.models import Course

class Command(BaseCommand):
    help = 'Deletes all existing courses and creates a new set of predefined courses with Thai descriptions.'

    def handle(self, *args, **options):
        # --- Step 1: Remove all existing courses ---
        self.stdout.write("Deleting all existing Course records...")
        delete_result = Course.objects.all().delete()
        self.stdout.write(f"Removed {delete_result[0]} courses.")

        # --- Step 2: Data Generation for New Bulk Creation ---
        self.stdout.write("Creating new course records...")
        items = [
            Course(
                course_name="Data Structures",
                course_code="CS302",
                description="การนำโครงสร้างข้อมูลที่ซับซ้อน เช่น ต้นไม้ ฮีป และแฮชเทเบิล มาประยุกต์ใช้งาน",
                credit=4
            ),
            Course(
                course_name="Multivariable Calculus",
                course_code="MATH250",
                description="เวกเตอร์ อนุพันธ์ย่อย ปริพันธ์หลายตัวแปร และทฤษฎีบทของกรีน",
                credit=4
            ),
            Course(
                course_name="Modern Political Theory",
                course_code="POLS315",
                description="การวิเคราะห์แนวคิดของนักคิดสำคัญ เช่น Locke, Rousseau และ Machiavelli",
                credit=3
            ),
            Course(
                course_name="Software Engineering Principles",
                course_code="CS460",
                description="แนวคิดวงจรชีวิตการพัฒนาซอฟต์แวร์ การทดสอบ และการทำงานเป็นทีม",
                credit=3
            ),
            Course(
                course_name="Biochemistry I",
                course_code="CHEM401",
                description="โครงสร้างและหน้าที่ของชีวโมเลกุล เมแทบอลิซึม และจลนศาสตร์เอนไซม์",
                credit=4
            ),
            Course(
                course_name="Classical Mythology",
                course_code="HUM100",
                description="การศึกษาเทพปกรณัมกรีกและโรมัน รวมถึงความสำคัญทางวัฒนธรรม",
                credit=3
            ),
            Course(
                course_name="Macroeconomics",
                course_code="ECON202",
                description="การศึกษาระบบเศรษฐกิจระดับมหภาค เช่น เงินเฟ้อ การว่างงาน และนโยบายการคลัง",
                credit=3
            ),
            Course(
                course_name="Creative Non-Fiction",
                course_code="ENGL215",
                description="เวิร์กช็อปการเขียนบันทึกส่วนตัว วารสารศาสตร์เชิงวรรณกรรม และบทความเชิงบรรยาย",
                credit=3
            ),
            Course(
                course_name="Computer Networks",
                course_code="CS430",
                description="การศึกษาโมเดล OSI, TCP/IP โปรโตคอลการส่งข้อมูล การเราท์ และความปลอดภัยเครือข่าย",
                credit=4
            ),
            Course(
                course_name="Fluid Mechanics",
                course_code="MECH370",
                description="การวิเคราะห์พฤติกรรมของของไหล การกระจายตัวของความดัน และพลศาสตร์การไหล",
                credit=3
            ),
        ]

        # Execute the new bulk creation
        Course.objects.bulk_create(items)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(items)} new courses."))
