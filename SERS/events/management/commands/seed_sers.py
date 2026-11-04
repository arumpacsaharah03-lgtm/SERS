from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Department, Event, Program


class Command(BaseCommand):
    help = "Create the standard SERS departments, programs, and sample events."

    departments = {
        "Agriculture": (
            "AGRI",
            [
                ("Agroforestry", "AGROFOR"),
                ("Animal Science", "ANSCI"),
                ("Extension Education", "EXTED"),
                ("Agronomy", "AGRON"),
            ],
        ),
        "College of Computer Studies": (
            "CCS",
            [("BSIT", "BSIT"), ("BSCS", "BSCS")],
        ),
        "Education": (
            "EDUC",
            [
                ("Bachelor of Elementary Education", "BEED"),
                ("BSE English", "BSE-ENG"),
                ("BSE Filipino", "BSE-FIL"),
                ("BSE Math", "BSE-MATH"),
            ],
        ),
    }

    events = [
        (
            "Innovation & Technology Summit",
            Event.Category.ACADEMIC,
            "University Convention Hall",
            "A showcase of student research, emerging technology, and industry workshops.",
            250,
        ),
        (
            "Green Campus Tree Planting",
            Event.Category.COMMUNITY,
            "Agriculture Research Field",
            "Restore native trees across the university research grounds.",
            120,
        ),
        (
            "Inter-College Sports Festival",
            Event.Category.SPORTS,
            "University Sports Complex",
            "A day of athletics, teamwork, and school spirit.",
            500,
        ),
        (
            "Future Educators Conference",
            Event.Category.CONFERENCE,
            "Education Building Auditorium",
            "Sessions on inclusive classrooms and learner-centered teaching.",
            180,
        ),
    ]

    def handle(self, *args, **options):
        for department_name, (code, programs) in self.departments.items():
            department, _ = Department.objects.update_or_create(
                code=code, defaults={"name": department_name}
            )
            for program_name, program_code in programs:
                Program.objects.update_or_create(
                    code=program_code,
                    defaults={"name": program_name, "department": department},
                )

        base_date = date.today() + timedelta(days=14)
        for index, (title, category, venue, description, capacity) in enumerate(
            self.events
        ):
            event_date = base_date + timedelta(days=index * 7)
            deadline = timezone.make_aware(
                datetime.combine(event_date - timedelta(days=4), time(23, 59))
            )
            Event.objects.update_or_create(
                title=title,
                defaults={
                    "description": description,
                    "category": category,
                    "event_date": event_date,
                    "start_time": time(9),
                    "end_time": time(16),
                    "venue": venue,
                    "registration_deadline": deadline,
                    "maximum_participants": capacity,
                    "status": Event.Status.PUBLISHED,
                },
            )
        self.stdout.write(self.style.SUCCESS("SERS starter data is ready."))
