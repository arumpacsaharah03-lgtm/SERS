from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("student/signup/", views.student_signup, name="student-signup"),
    path("student/login/", views.student_login, name="student-login"),
    path("student/logout/", views.student_logout, name="student-logout"),
    path("student/dashboard/", views.student_dashboard, name="student-dashboard"),
    path("student/events/", views.student_events, name="student-events"),
    path(
        "student/events/<int:event_id>/register/",
        views.student_register,
        name="student-register",
    ),
    path(
        "student/registrations/",
        views.student_registrations,
        name="student-registrations",
    ),
    path("student/profile/", views.student_profile, name="student-profile"),
]
