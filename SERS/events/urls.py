from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("csrf/", views.csrf_token, name="csrf"),
    path("auth/signup/", views.signup, name="signup"),
    path("auth/login/", views.sign_in, name="login"),
    path("auth/logout/", views.sign_out, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("events/", views.event_list, name="event-list"),
    path("events/<int:event_id>/", views.event_detail, name="event-detail"),
    path("registrations/", views.registration_list, name="registration-list"),
    path(
        "registrations/<int:registration_id>/status/",
        views.registration_status,
        name="registration-status",
    ),
    path("reports/", views.reports, name="reports"),
]
