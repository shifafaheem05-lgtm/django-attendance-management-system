from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("students/", views.student_list, name="student_list"),
    path("students/add/", views.add_student, name="add_student"),
    path("students/<int:id>/", views.student_detail, name="student_detail"),
    path("students/update/<int:id>/", views.update_student, name="update_student"),
    path("students/delete/<int:id>/", views.delete_student, name="delete_student"),
    path("attendance/", views.mark_attendance, name="mark_attendance"),
    path("attendance/history/", views.attendance_history, name="attendance_history"),
    path("report/", views.report, name="report"),
    path("report/export/", views.export_report_csv, name="export_report_csv"),
]
