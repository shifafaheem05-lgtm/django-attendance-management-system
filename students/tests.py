from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Attendance, Student
from .services import percentage, student_stats


class BaseTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("teacher", password="pass12345")
        self.s1 = Student.objects.create(name="Ayesha", roll_no=1, student_class="VIII")
        self.s2 = Student.objects.create(name="Bilal", roll_no=2, student_class="VIII")
        self.client.login(username="teacher", password="pass12345")


class AuthTests(BaseTest):
    def test_login_required(self):
        self.client.logout()
        for name in ["home", "student_list", "report", "attendance_history", "mark_attendance"]:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn("/login/", r["Location"])

    def test_delete_requires_post(self):
        r = self.client.get(reverse("delete_student", args=[self.s1.id]))
        self.assertEqual(r.status_code, 405)
        self.assertTrue(Student.objects.filter(id=self.s1.id).exists())


class ServiceTests(BaseTest):
    def test_percentage(self):
        self.assertEqual(percentage(3, 4), 75.0)
        self.assertEqual(percentage(0, 0), 0.0)

    def test_stats_and_low_flag(self):
        today = date.today()
        for i in range(4):
            Attendance.objects.create(student=self.s1, date=today - timedelta(days=i), status="Present")
            Attendance.objects.create(
                student=self.s2, date=today - timedelta(days=i),
                status="Present" if i == 0 else "Absent",
            )
        rows = {r["student"].name: r for r in student_stats()}
        self.assertEqual(rows["Ayesha"]["percentage"], 100.0)
        self.assertFalse(rows["Ayesha"]["low"])
        self.assertEqual(rows["Bilal"]["percentage"], 25.0)
        self.assertTrue(rows["Bilal"]["low"])

    def test_date_range_filter(self):
        today = date.today()
        Attendance.objects.create(student=self.s1, date=today, status="Present")
        Attendance.objects.create(student=self.s1, date=today - timedelta(days=30), status="Absent")
        row = student_stats(date_from=today - timedelta(days=5))[0]
        self.assertEqual((row["present"], row["absent"]), (1, 0))


class ViewTests(BaseTest):
    def test_mark_attendance_saves_and_updates(self):
        url = reverse("mark_attendance")
        data = {"date": "2026-01-05", f"status_{self.s1.id}": "Present", f"status_{self.s2.id}": "Absent"}
        self.client.post(url, data)
        self.assertEqual(Attendance.objects.count(), 2)
        data[f"status_{self.s2.id}"] = "Present"
        self.client.post(url, data)  # re-submitting updates, never duplicates
        self.assertEqual(Attendance.objects.count(), 2)
        self.assertEqual(Attendance.objects.get(student=self.s2).status, "Present")

    def test_mark_attendance_invalid_date(self):
        r = self.client.post(reverse("mark_attendance"), {"date": "bad"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Attendance.objects.count(), 0)

    def test_history_badge_and_filter(self):
        Attendance.objects.create(student=self.s1, date=date.today(), status="Absent")
        r = self.client.get(reverse("attendance_history"), {"status": "Absent"})
        self.assertContains(r, "bg-danger")
        r = self.client.get(reverse("attendance_history"), {"status": "Present"})
        self.assertNotContains(r, "Ayesha")

    def test_student_search(self):
        r = self.client.get(reverse("student_list"), {"q": "bil"})
        self.assertContains(r, "Bilal")
        self.assertNotContains(r, "Ayesha")

    def test_csv_export(self):
        Attendance.objects.create(student=self.s1, date=date.today(), status="Present")
        r = self.client.get(reverse("export_report_csv"))
        self.assertEqual(r["Content-Type"], "text/csv")
        self.assertIn("Ayesha", r.content.decode())

    def test_csv_formula_injection_is_neutralised(self):
        Student.objects.create(name="=cmd()", roll_no=9, student_class="X")
        body = self.client.get(reverse("export_report_csv")).content.decode()
        self.assertIn("'=cmd()", body)

    def test_pages_render(self):
        Attendance.objects.create(student=self.s1, date=date.today(), status="Present")
        for name, args in [("home", []), ("report", []), ("student_detail", [self.s1.id]),
                           ("add_student", []), ("update_student", [self.s1.id])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)


class SeedTests(TestCase):
    def test_seed_demo(self):
        call_command("seed_demo", verbosity=0)
        self.assertEqual(Student.objects.count(), 8)
        self.assertTrue(Attendance.objects.exists())
