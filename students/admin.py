from django.contrib import admin

from .models import Attendance, Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("roll_no", "name", "student_class", "section")
    list_filter = ("student_class", "section")
    search_fields = ("name", "roll_no")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "status")
    list_filter = ("status", "date")
    search_fields = ("student__name",)
