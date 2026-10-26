import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from students.models import Attendance, Student

NAMES = ["Ayesha Khan", "Bilal Ahmed", "Hina Malik", "Usman Ali", "Sara Noor",
         "Hamza Iqbal", "Zainab Fatima", "Ali Raza"]


class Command(BaseCommand):
    help = "Create fictional demo students and 30 days of attendance (no real data)."

    def handle(self, *args, **options):
        random.seed(7)
        today = timezone.localdate()
        for i, name in enumerate(NAMES, start=1):
            student, _ = Student.objects.get_or_create(
                roll_no=i,
                defaults={"name": name, "student_class": "VIII", "section": "A"},
            )
            n = 0
            for d in range(30):
                day = today - timedelta(days=d)
                if day.weekday() >= 5:
                    continue
                n += 1
                # The last two students get deliberately low attendance so the
                # "low attendance" warning is visible in the demo.
                if i == len(NAMES):
                    absent = n % 2 == 0          # ~50% present
                elif i == len(NAMES) - 1:
                    absent = n % 3 == 0          # ~67% present
                else:
                    absent = random.random() > 0.92
                Attendance.objects.update_or_create(
                    student=student, date=day,
                    defaults={"status": "Absent" if absent else "Present"},
                )
        self.stdout.write(self.style.SUCCESS(f"Demo data ready: {Student.objects.count()} students."))
