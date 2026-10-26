"""Attendance calculation helpers shared by views, exports and tests."""
from django.db.models import Count, Q

from .models import Attendance, Student

LOW_ATTENDANCE_THRESHOLD = 75  # percent


def percentage(present, total):
    return round(present * 100 / total, 1) if total else 0.0


def student_stats(date_from=None, date_to=None, query=None, student_class=None):
    """Per-student present/absent totals and percentage, in a single query."""
    students = Student.objects.all()
    if query:
        students = students.filter(Q(name__icontains=query) | Q(roll_no__icontains=query))
    if student_class:
        students = students.filter(student_class=student_class)

    in_range = Q()
    if date_from:
        in_range &= Q(attendance__date__gte=date_from)
    if date_to:
        in_range &= Q(attendance__date__lte=date_to)

    students = students.annotate(
        present=Count("attendance", filter=in_range & Q(attendance__status="Present")),
        absent=Count("attendance", filter=in_range & Q(attendance__status="Absent")),
    ).order_by("student_class", "section", "roll_no")

    rows = []
    for s in students:
        total = s.present + s.absent
        pct = percentage(s.present, total)
        rows.append({
            "student": s,
            "present": s.present,
            "absent": s.absent,
            "total": total,
            "percentage": pct,
            "low": total > 0 and pct < LOW_ATTENDANCE_THRESHOLD,
        })
    return rows


def daily_summary(days=7):
    """Present/absent counts for the most recent `days` dates that have records."""
    dates = list(
        Attendance.objects.order_by("-date").values_list("date", flat=True).distinct()[:days]
    )
    dates.reverse()
    data = []
    for d in dates:
        qs = Attendance.objects.filter(date=d)
        data.append({
            "date": d.strftime("%d %b"),
            "present": qs.filter(status="Present").count(),
            "absent": qs.filter(status="Absent").count(),
        })
    return data
