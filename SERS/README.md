# School Event Registration System (SERS)

This folder is the standalone SERS application: Django serves the
server-rendered HTML5/CSS3/Bootstrap 5 student portal, JSON API, and admin site.
It can be copied to a Windows laptop and run independently of the Next.js demo
in the parent project.

## Database tables

The Django migration creates these domain tables:

- `Departments`
- `Programs`
- `Students`
- `Events`
- `Registrations`

Django also creates its secure authentication, session, permission, and admin
tables. `Registrations` has a database-level unique constraint on
`(student_id, event_id)`, so duplicate event registration is impossible.

## Windows 10 setup

### Prerequisites

1. Install Python 3.12 and enable **Add Python to PATH**.
2. Install MySQL 8 or MariaDB 10.5 or later. MariaDB 10.4 (including older
   XAMPP releases) is not supported by Django 5.2.
3. Open MySQL Workbench and run `database/create_database.sql`.
4. Create a dedicated `sers_user` account with privileges on `sers_db`, and set
   that account's username and password in `.env`. Keep credentials out of SQL
   files and source control.

### Automatic setup

1. Copy `.env.example` to `.env`.
2. Set `MYSQL_USER` and `MYSQL_PASSWORD` in `.env` to a database account with
   access to `sers_db`.
3. Double-click `setup_windows.bat`.
4. Run `venv\Scripts\python.exe manage.py createsuperuser` to create the first
   authorized administrator.
5. Double-click `run_windows.bat`.
6. Open `http://127.0.0.1:8000/student/signup/` to create a student account,
   or `http://127.0.0.1:8000/admin/` to manage events and records.

The Django administration panel is available at `http://127.0.0.1:8000/admin/`.
Its SERS dashboard provides database-backed counts and permission-aware
shortcuts; all model add, change, search, and review pages remain Django Admin.

## Manual setup

```bat
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_sers
python manage.py createsuperuser
python manage.py runserver
```

The student portal is served by Django at `/student/signup/`,
`/student/login/`, `/student/dashboard/`, `/student/events/`,
`/student/registrations/`, and `/student/profile/`. Its forms use Django
sessions, CSRF protection, and the same records as the API and admin.
Student signup asks for the existing numeric school ID and requires the
institutional email to match `lastname.StudentIDNumber@msusnd.edu.ph` (for
example, `doe.1003899@msusnd.edu.ph`). The last name is lowercased for the
address; existing accounts are not automatically renamed.

## API routes

| Method | Route | Access |
|---|---|---|
| GET | `/api/health/` | Public |
| GET | `/api/csrf/` | Public |
| POST | `/api/auth/signup/` | Public |
| POST | `/api/auth/login/` | Public |
| POST | `/api/auth/logout/` | Signed in |
| GET, PATCH | `/api/profile/` | Student |
| GET | `/api/events/` | Signed in |
| POST | `/api/events/` | Administrator |
| GET, PATCH, DELETE | `/api/events/<id>/` | Signed in / Administrator |
| GET, POST | `/api/registrations/` | Student or Administrator |
| PATCH | `/api/registrations/<id>/status/` | Administrator |
| GET | `/api/reports/` | Administrator |

All write operations validate and allowlist submitted fields. Browser clients
must first call `/api/csrf/` and send the returned token in the
`X-CSRFToken` header. Authentication uses Django's secure session cookie.

## Testing

Tests use an isolated SQLite database and do not modify MySQL:

```bat
set USE_SQLITE=1
venv\Scripts\python manage.py test
```

SQLite is available for local testing and development only. It does not satisfy
a MySQL course requirement. Use a supported MySQL/MariaDB server for the
configured `.env` database.

## Frontend note

The Next.js code in the parent project's `src/` directory remains a separate
presentation prototype; this Django application is the server-rendered
coursework frontend and backend.
