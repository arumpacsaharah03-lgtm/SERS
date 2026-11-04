# Generated for SERS Django 5.2.
import django.db.models.deletion
import events.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120, unique=True)),
                ("code", models.CharField(max_length=20, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "Departments", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("Academic", "Academic"),
                            ("Community", "Community"),
                            ("Sports", "Sports"),
                            ("Conference", "Conference"),
                            ("Cultural", "Cultural"),
                            ("Other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                ("event_date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("venue", models.CharField(max_length=200)),
                ("registration_deadline", models.DateTimeField()),
                ("maximum_participants", models.PositiveIntegerField()),
                (
                    "image",
                    models.ImageField(
                        blank=True, null=True, upload_to="events/%Y/%m/"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Draft", "Draft"),
                            ("Published", "Published"),
                            ("Completed", "Completed"),
                            ("Cancelled", "Cancelled"),
                        ],
                        default="Draft",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "Events",
                "ordering": ["event_date", "start_time"],
                "indexes": [
                    models.Index(
                        fields=["status", "event_date"],
                        name="Events_status_event_date_idx",
                    ),
                    models.Index(
                        fields=["category"], name="Events_category_idx"
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Program",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=150)),
                ("code", models.CharField(max_length=30, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="programs",
                        to="events.department",
                    ),
                ),
            ],
            options={
                "db_table": "Programs",
                "ordering": ["department__name", "name"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("department", "name"),
                        name="unique_program_per_department",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "student_id",
                    models.CharField(
                        default=events.models.generate_student_id,
                        max_length=30,
                        unique=True,
                    ),
                ),
                ("middle_name", models.CharField(blank=True, max_length=100)),
                (
                    "year_level",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "1st Year"),
                            (2, "2nd Year"),
                            (3, "3rd Year"),
                            (4, "4th Year"),
                        ]
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="students",
                        to="events.department",
                    ),
                ),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="students",
                        to="events.program",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="student",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "Students",
                "ordering": ["user__last_name", "user__first_name"],
            },
        ),
        migrations.CreateModel(
            name="Registration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Pending", "Pending"),
                            ("Approved", "Approved"),
                            ("Rejected", "Rejected"),
                        ],
                        default="Pending",
                        max_length=20,
                    ),
                ),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("rejection_reason", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="registrations",
                        to="events.event",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_registrations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="registrations",
                        to="events.student",
                    ),
                ),
            ],
            options={
                "db_table": "Registrations",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["status", "created_at"],
                        name="Regs_status_created_idx",
                    ),
                    models.Index(
                        fields=["event", "status"],
                        name="Regs_event_status_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("student", "event"),
                        name="unique_student_event",
                    )
                ],
            },
        ),
    ]
