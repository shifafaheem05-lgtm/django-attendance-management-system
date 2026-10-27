# Django Attendance Management System

**Live demo:** https://shifafaheem.pythonanywhere.com

Demo login: `demo` / `Demo@2026` (fictional data only)

A web-based student attendance system built with **Python and Django**. Teachers log in to manage students, mark daily attendance, review history, and generate attendance reports with percentage tracking, low-attendance warnings and CSV export.

## Key Features

- **Student management (CRUD)** – add, view, edit and delete students (name, roll number, class, section) with unique roll numbers.
- **Daily attendance marking** – pick a date and class, mark each student Present/Absent, with *All Present / All Absent* shortcuts. Re-saving a date updates records instead of creating duplicates, and existing marks are pre-filled.
- **Attendance history** – full log of every record with colour-coded status badges.
- **Dashboard** – total students, today's present/absent counts, today's attendance percentage and a reminder when attendance has not been marked yet.
- **Django admin panel** – search and filter students and attendance records.

## Advanced Features

- **Authentication** – teacher login/logout; every page is protected with `login_required`.
- **Attendance percentage per student** – calculated with a single annotated database query (no per-student query loop).
- **Low-attendance warning** – students below 75% (configurable in `students/services.py`) are highlighted on the report, dashboard and student profile.
- **Charts** – stacked bar chart of the last 7 recorded days (Chart.js).
- **Search, filter and pagination** – search students by name or roll number, filter by class, filter history by status and date range.
- **Date-range reports** – report for any period, filtered by class or student.
- **CSV export** – download the filtered report; cells are sanitised against spreadsheet formula injection.
- **Student profile page** – individual attendance summary and recent records.
- **Safer actions** – deletes are POST-only with a confirmation prompt, and flash messages confirm every action.
- **Automated tests** – 13 tests covering authentication, attendance logic, filters, CSV export and the demo-data command.
- **Demo data command** – `python manage.py seed_demo` creates fictional students and 30 days of attendance so you can try the app instantly.
- **Environment-based configuration** – `SECRET_KEY`, `DEBUG`, allowed hosts and time zone are read from environment variables.

## Tech Stack

Python · Django · SQLite · HTML · Bootstrap 5 · Chart.js

## Getting Started

```bash
git clone https://github.com/shifafaheem05-lgtm/django-attendance-management-system.git
cd django-attendance-management-system

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # this account is your teacher login
python manage.py seed_demo         # optional: fictional demo data
python manage.py runserver
```

Open <http://127.0.0.1:8000/> and log in.

### Run the tests

```bash
python manage.py test
```

### Environment variables (optional for local use)

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key – **set this in production** | insecure dev key |
| `DJANGO_DEBUG` | `True` / `False` | `True` |
| `DJANGO_ALLOWED_HOSTS` | comma-separated hostnames | empty |
| `DJANGO_TIME_ZONE` | time zone name | `Asia/Karachi` |

## Project Structure

```
attendance/            Django project (settings, root urls)
students/
├── models.py          Student, Attendance
├── views.py           Pages, filters, CSV export
├── services.py        Percentage / statistics logic
├── management/        seed_demo command
├── templates/         Bootstrap templates (+ login page)
└── tests.py           Automated tests
```

## Possible Future Improvements

Student/parent portal, email or SMS alerts for low attendance, Excel/PDF export, QR-code or face-recognition check-in.

## Author

**Shifa Faheem** – [GitHub](https://github.com/shifafaheem05-lgtm)
