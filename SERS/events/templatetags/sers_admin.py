from django import template
from django.urls import reverse

from events.models import Event, Registration, Student

register = template.Library()


@register.simple_tag
def portal_stats(user):
    stats = []
    definitions = [
        (
            "events.view_student",
            "Students",
            lambda: Student.objects.filter(is_active=True).count(),
            "bi-people",
            "admin:events_student_changelist",
            "blue",
        ),
        (
            "events.view_event",
            "Published events",
            lambda: Event.objects.filter(status=Event.Status.PUBLISHED).count(),
            "bi-calendar-event",
            "admin:events_event_changelist",
            "purple",
        ),
        (
            "events.view_registration",
            "Registrations",
            lambda: Registration.objects.count(),
            "bi-ticket-perforated",
            "admin:events_registration_changelist",
            "green",
        ),
        (
            "events.view_registration",
            "Pending review",
            lambda: Registration.objects.filter(
                status=Registration.Status.PENDING
            ).count(),
            "bi-clock-history",
            "admin:events_registration_changelist",
            "orange",
        ),
    ]
    for permission, label, count, icon, route, tone in definitions:
        if user.has_perm(permission):
            url = reverse(route)
            if label == "Pending review":
                url += "?status__exact=Pending"
            stats.append(
                {
                    "label": label,
                    "value": count(),
                    "icon": icon,
                    "url": url,
                    "tone": tone,
                }
            )
    return stats


@register.simple_tag
def portal_shortcuts(user):
    definitions = [
        (
            "events.add_event",
            "Create an event",
            "Publish a new campus activity.",
            "bi-calendar-plus",
            "admin:events_event_add",
        ),
        (
            "events.view_registration",
            "Review registrations",
            "Approve or update student requests.",
            "bi-clipboard-check",
            "admin:events_registration_changelist",
        ),
        (
            "events.view_student",
            "Manage students",
            "Browse student accounts and programs.",
            "bi-person-lines-fill",
            "admin:events_student_changelist",
        ),
    ]
    return [
        {
            "label": label,
            "description": description,
            "icon": icon,
            "url": reverse(route),
        }
        for permission, label, description, icon, route in definitions
        if user.has_perm(permission)
    ]
