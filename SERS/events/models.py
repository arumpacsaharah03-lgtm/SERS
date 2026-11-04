import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def generate_student_id():
    return f"SERS-{timezone.now():%Y}-{uuid.uuid4().hex[:6].upper()}"


class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Departments"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Program(models.Model):
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="programs"
    )
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Programs"
        ordering = ["department__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"], name="unique_program_per_department"
            )
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Student(models.Model):
    class YearLevel(models.IntegerChoices):
        FIRST = 1, "1st Year"
        SECOND = 2, "2nd Year"
        THIRD = 3, "3rd Year"
        FOURTH = 4, "4th Year"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student"
    )
    student_id = models.CharField(
        max_length=30, unique=True, default=generate_student_id
    )
    middle_name = models.CharField(max_length=100, blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="students"
    )
    program = models.ForeignKey(
        Program, on_delete=models.PROTECT, related_name="students"
    )
    year_level = models.PositiveSmallIntegerField(choices=YearLevel.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Students"
        ordering = ["user__last_name", "user__first_name"]

    def clean(self):
        if self.program_id and self.department_id:
            if self.program.department_id != self.department_id:
                raise ValidationError(
                    {"program": "The selected program is not in this department."}
                )

    @property
    def full_name(self):
        parts = [self.user.first_name, self.middle_name, self.user.last_name]
        return " ".join(part for part in parts if part).strip()

    def __str__(self):
        return f"{self.student_id} — {self.full_name}"


class Event(models.Model):
    class Category(models.TextChoices):
        ACADEMIC = "Academic", "Academic"
        COMMUNITY = "Community", "Community"
        SPORTS = "Sports", "Sports"
        CONFERENCE = "Conference", "Conference"
        CULTURAL = "Cultural", "Cultural"
        OTHER = "Other", "Other"

    class Status(models.TextChoices):
        DRAFT = "Draft", "Draft"
        PUBLISHED = "Published", "Published"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=Category.choices)
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue = models.CharField(max_length=200)
    registration_deadline = models.DateTimeField()
    maximum_participants = models.PositiveIntegerField()
    image = models.ImageField(upload_to="events/%Y/%m/", blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Events"
        ordering = ["event_date", "start_time"]
        indexes = [
            models.Index(
                fields=["status", "event_date"],
                name="Events_status_event_date_idx",
            ),
            models.Index(fields=["category"], name="Events_category_idx"),
        ]

    def clean(self):
        errors = {}
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            errors["end_time"] = "End time must be later than start time."
        if self.maximum_participants is not None and self.maximum_participants < 1:
            errors["maximum_participants"] = "Capacity must be at least one."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title


class Registration(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        REJECTED = "Rejected", "Rejected"

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="registrations"
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="registrations"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_registrations",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Registrations"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "event"], name="unique_student_event"
            )
        ]
        indexes = [
            models.Index(
                fields=["status", "created_at"],
                name="Regs_status_created_idx",
            ),
            models.Index(
                fields=["event", "status"],
                name="Regs_event_status_idx",
            ),
        ]

    def __str__(self):
        return f"{self.student.full_name} — {self.event.title}"
