import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import StudentForm
from .models import Attendance, Student
from .services import (
    LOW_ATTENDANCE_THRESHOLD,
    daily_summary,
    percentage,
    student_stats,
)


def _parse_date(value):
    """Return a date from 'YYYY-MM-DD' or None if empty/invalid."""
    from datetime import date

    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


@login_required
def home(request):
    today = timezone.localdate()
    total_students = Student.objects.count()
    present = Attendance.objects.filter(date=today, status="Present").count()
    absent = Attendance.objects.filter(date=today, status="Absent").count()
    marked = present + absent

    low_students = [r for r in student_stats() if r["low"]]

    context = {
        "total_students": total_students,
        "present": present,
        "absent": absent,
        "not_marked": max(total_students - marked, 0),
        "today_percentage": percentage(present, marked),
        "low_students": low_students[:5],
        "low_count": len(low_students),
        "threshold": LOW_ATTENDANCE_THRESHOLD,
        "chart_data": daily_summary(7),
    }
    return render(request, "students/home.html", context)


@login_required
def student_list(request):
    query = request.GET.get("q", "").strip()
    cls = request.GET.get("class", "").strip()

    students = Student.objects.all().order_by("student_class", "section", "roll_no")
    if query:
        students = students.filter(Q(name__icontains=query) | Q(roll_no__icontains=query))
    if cls:
        students = students.filter(student_class=cls)

    page = Paginator(students, 10).get_page(request.GET.get("page"))
    classes = Student.objects.order_by("student_class").values_list("student_class", flat=True).distinct()
    return render(request, "students/student_list.html", {
        "page": page, "q": query, "selected_class": cls, "classes": classes,
    })


@login_required
def student_detail(request, id):
    student = get_object_or_404(Student, id=id)
    records = student.attendance_set.order_by("-date")
    present = records.filter(status="Present").count()
    total = records.count()
    pct = percentage(present, total)
    return render(request, "students/student_detail.html", {
        "student": student,
        "records": records[:60],
        "present": present,
        "absent": total - present,
        "total": total,
        "percentage": pct,
        "low": total > 0 and pct < LOW_ATTENDANCE_THRESHOLD,
        "threshold": LOW_ATTENDANCE_THRESHOLD,
    })


@login_required
def add_student(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        student = form.save()
        messages.success(request, f"{student.name} was added.")
        return redirect("student_list")
    return render(request, "students/add_student.html", {"form": form})


@login_required
def update_student(request, id):
    student = get_object_or_404(Student, id=id)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{student.name} was updated.")
        return redirect("student_list")
    return render(request, "students/update_student.html", {"form": form})


@login_required
@require_POST
def delete_student(request, id):
    student = get_object_or_404(Student, id=id)
    name = student.name
    student.delete()
    messages.success(request, f"{name} was deleted.")
    return redirect("student_list")


@login_required
def mark_attendance(request):
    cls = request.GET.get("class", "").strip()
    students = Student.objects.all().order_by("student_class", "section", "roll_no")
    if cls:
        students = students.filter(student_class=cls)
    classes = Student.objects.order_by("student_class").values_list("student_class", flat=True).distinct()

    if request.method == "POST":
        date = _parse_date(request.POST.get("date"))
        if not date:
            messages.error(request, "Please choose a valid date.")
        else:
            saved = 0
            for student in students:
                status = request.POST.get(f"status_{student.id}")
                if status in ("Present", "Absent"):
                    Attendance.objects.update_or_create(
                        student=student, date=date, defaults={"status": status}
                    )
                    saved += 1
            messages.success(request, f"Attendance saved for {saved} students on {date:%d %b %Y}.")
            return redirect("attendance_history")

    # Pre-fill with any attendance already saved for the chosen date.
    date = _parse_date(request.GET.get("date")) or timezone.localdate()
    existing = dict(
        Attendance.objects.filter(date=date).values_list("student_id", "status")
    )
    rows = [{"student": s, "status": existing.get(s.id, "Present")} for s in students]
    return render(request, "students/attendance.html", {
        "rows": rows, "date": date, "classes": classes, "selected_class": cls,
    })


@login_required
def attendance_history(request):
    qs = Attendance.objects.select_related("student").order_by("-date", "student__roll_no")

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    date_from = _parse_date(request.GET.get("from"))
    date_to = _parse_date(request.GET.get("to"))

    if q:
        qs = qs.filter(Q(student__name__icontains=q) | Q(student__roll_no__icontains=q))
    if status in ("Present", "Absent"):
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "students/attendance_history.html", {
        "page": page, "q": q, "status": status,
        "date_from": request.GET.get("from", ""), "date_to": request.GET.get("to", ""),
    })


def _report_filters(request):
    return {
        "date_from": _parse_date(request.GET.get("from")),
        "date_to": _parse_date(request.GET.get("to")),
        "query": request.GET.get("q", "").strip(),
        "student_class": request.GET.get("class", "").strip(),
    }


@login_required
def report(request):
    rows = student_stats(**_report_filters(request))
    classes = Student.objects.order_by("student_class").values_list("student_class", flat=True).distinct()
    return render(request, "students/report.html", {
        "reports": rows,
        "classes": classes,
        "threshold": LOW_ATTENDANCE_THRESHOLD,
        "low_count": sum(1 for r in rows if r["low"]),
        "q": request.GET.get("q", ""),
        "selected_class": request.GET.get("class", ""),
        "date_from": request.GET.get("from", ""),
        "date_to": request.GET.get("to", ""),
    })


def _csv_safe(value):
    """Prevent spreadsheet formula injection in exported cells."""
    text = str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


@login_required
def export_report_csv(request):
    rows = student_stats(**_report_filters(request))
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="attendance_report_{timezone.localdate():%Y%m%d}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(["Roll No", "Name", "Class", "Section", "Present", "Absent", "Total", "Percentage", "Status"])
    for r in rows:
        s = r["student"]
        writer.writerow([
            s.roll_no, _csv_safe(s.name), _csv_safe(s.student_class), _csv_safe(s.section),
            r["present"], r["absent"], r["total"], f'{r["percentage"]}%',
            "Low attendance" if r["low"] else "OK",
        ])
    return response
