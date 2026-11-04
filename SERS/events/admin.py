from django.contrib import admin

from .models import Department, Event, Program, Registration, Student

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "department")
    list_filter = ("department",)
    search_fields = ("name", "code")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "student_id",
        "full_name",
        "department",
        "program",
        "year_level",
        "is_active",
    )
    list_filter = ("department", "program", "year_level", "is_active")
    search_fields = (
        "student_id",
        "user__first_name",
        "user__last_name",
        "user__email",
    )
    autocomplete_fields = ("user",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "event_date",
        "venue",
        "status",
        "maximum_participants",
    )
    list_filter = ("status", "category", "event_date")
    search_fields = ("title", "description", "venue")
    date_hierarchy = "event_date"


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("student", "event", "status", "created_at", "reviewed_by")
    list_filter = ("status", "event", "created_at")
    search_fields = (
        "student__student_id",
        "student__user__first_name",
        "student__user__last_name",
        "event__title",
    )
    autocomplete_fields = ("student", "event", "reviewed_by")
