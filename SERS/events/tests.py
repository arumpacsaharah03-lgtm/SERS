from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Department, Event, Program, Registration, Student


class SERSWorkflowTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Education", code="EDUC")
        self.program = Program.objects.create(
            department=self.department, name="BSE English", code="BSE-ENG"
        )
        self.event = Event.objects.create(
            title="Future Educators Conference",
            description="Teaching conference.",
            category=Event.Category.CONFERENCE,
            event_date=date.today() + timedelta(days=20),
            start_time=time(9),
            end_time=time(16),
            venue="Education Auditorium",
            registration_deadline=timezone.now() + timedelta(days=10),
            maximum_participants=50,
            status=Event.Status.PUBLISHED,
        )

    def test_complete_student_registration_and_admin_review(self):
        signup = self.client.post(
            reverse("events:signup"),
            data={
                "firstName": "Maria",
                "middleName": "Lopez",
                "lastName": "Santos",
                "studentId": "1003899",
                "departmentId": self.department.id,
                "programId": self.program.id,
                "yearLevel": 3,
                "email": "santos.1003899@msusnd.edu.ph",
                "password": "StrongPass123!",
                "confirmPassword": "StrongPass123!",
            },
        )
        self.assertEqual(signup.status_code, 201, signup.content)
        self.assertEqual(signup.json()["student"]["studentId"], "1003899")

        login_response = self.client.post(
            reverse("events:login"),
            data={
                "email": "santos.1003899@msusnd.edu.ph",
                "password": "StrongPass123!",
                "role": "student",
            },
        )
        self.assertEqual(login_response.status_code, 200)

        registration_response = self.client.post(
            reverse("events:registration-list"), data={"eventId": self.event.id}
        )
        self.assertEqual(registration_response.status_code, 201)
        self.assertEqual(
            registration_response.json()["registration"]["status"],
            Registration.Status.PENDING,
        )

        duplicate = self.client.post(
            reverse("events:registration-list"), data={"eventId": self.event.id}
        )
        self.assertEqual(duplicate.status_code, 400)

        admin = User.objects.create_user(
            username="admin@sers.edu",
            email="admin@sers.edu",
            password="AdminPass123!",
            is_staff=True,
        )
        self.client.force_login(admin)
        registration = Registration.objects.get()
        approval = self.client.patch(
            reverse(
                "events:registration-status",
                kwargs={"registration_id": registration.id},
            ),
            data='{"status":"Approved"}',
            content_type="application/json",
        )
        self.assertEqual(approval.status_code, 200, approval.content)
        registration.refresh_from_db()
        self.assertEqual(registration.status, Registration.Status.APPROVED)
        self.assertEqual(registration.reviewed_by, admin)

    def test_student_cannot_access_admin_report(self):
        user = User.objects.create_user(
            username="student@students.sers.edu",
            email="student@students.sers.edu",
            password="StrongPass123!",
        )
        Student.objects.create(
            user=user,
            department=self.department,
            program=self.program,
            year_level=1,
        )
        self.client.force_login(user)
        response = self.client.get(reverse("events:reports"))
        self.assertEqual(response.status_code, 403)

    def test_program_must_match_department(self):
        other_department = Department.objects.create(
            name="Agriculture", code="AGRI"
        )
        user = User.objects.create_user(
            username="mismatch@students.sers.edu",
            email="mismatch@students.sers.edu",
            password="StrongPass123!",
        )
        student = Student(
            user=user,
            department=other_department,
            program=self.program,
            year_level=1,
        )
        with self.assertRaisesMessage(
            Exception, "The selected program is not in this department."
        ):
            student.full_clean()

    def test_student_frontend_signup_login_and_event_registration(self):
        signup_page = self.client.get(reverse("student-signup"))
        self.assertEqual(signup_page.status_code, 200)
        self.assertTemplateUsed(signup_page, "events/student_signup.html")
        self.assertContains(signup_page, "Create student account")

        signup_response = self.client.post(
            reverse("student-signup"),
            data={
                "first_name": "Maria",
                "middle_name": "Lopez",
                "last_name": "Santos",
                "student_id": "1003899",
                "department": self.department.id,
                "program": self.program.id,
                "year_level": 3,
                "email": "santos.1003899@msusnd.edu.ph",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
        )
        self.assertRedirects(signup_response, reverse("student-login"))
        user = User.objects.get(username="santos.1003899@msusnd.edu.ph")
        self.assertTrue(hasattr(user, "student"))
        self.assertEqual(user.student.student_id, "1003899")

        login_page = self.client.get(reverse("student-login"))
        self.assertEqual(login_page.status_code, 200)
        self.assertTemplateUsed(login_page, "events/student_login.html")

        login_response = self.client.post(
            reverse("student-login"),
            data={
                "email": "santos.1003899@msusnd.edu.ph",
                "password": "StrongPass123!",
            },
        )
        self.assertRedirects(login_response, reverse("student-dashboard"))
        self.assertEqual(
            self.client.get(reverse("student-dashboard")).status_code, 200
        )
        self.assertEqual(self.client.get(reverse("student-events")).status_code, 200)

        register_response = self.client.post(
            reverse("student-register", kwargs={"event_id": self.event.id})
        )
        self.assertRedirects(register_response, reverse("student-events"))
        self.assertTrue(
            Registration.objects.filter(
                student=user.student, event=self.event
            ).exists()
        )
        self.assertEqual(
            self.client.get(reverse("student-registrations")).status_code, 200
        )

    def test_student_signup_rejects_email_not_matching_last_name_and_id(self):
        response = self.client.post(
            reverse("student-signup"),
            data={
                "first_name": "Jane",
                "middle_name": "",
                "last_name": "Doe",
                "student_id": "1003899",
                "department": self.department.id,
                "program": self.program.id,
                "year_level": 1,
                "email": "jane.doe@msusnd.edu.ph",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Use your lowercase last name")
        self.assertFalse(User.objects.filter(username="jane.doe@msusnd.edu.ph").exists())

    def test_api_signup_rejects_non_numeric_student_id(self):
        response = self.client.post(
            reverse("events:signup"),
            data={
                "firstName": "Jane",
                "lastName": "Doe",
                "studentId": "SERS-1003899",
                "departmentId": self.department.id,
                "programId": self.program.id,
                "yearLevel": 1,
                "email": "doe.1003899@msusnd.edu.ph",
                "password": "StrongPass123!",
                "confirmPassword": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("studentId", response.json()["errors"])

    def test_student_pages_require_a_student_account(self):
        response = self.client.get(reverse("student-events"))
        self.assertRedirects(
            response,
            f"{reverse('student-login')}?next={reverse('student-events')}",
        )

        admin = User.objects.create_user(
            username="admin@sers.edu",
            email="admin@sers.edu",
            password="AdminPass123!",
            is_staff=True,
        )
        self.client.force_login(admin)
        admin_response = self.client.get(reverse("student-events"))
        self.assertRedirects(admin_response, reverse("admin:index"))

    def test_admin_portal_dashboard_and_model_pages(self):
        admin_user = User.objects.create_superuser(
            username="portal-admin",
            email="admin@sers.edu",
            password="AdminPass123!",
        )
        self.client.force_login(admin_user)

        dashboard = self.client.get(reverse("admin:index"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertTemplateUsed(dashboard, "admin/index.html")
        self.assertContains(dashboard, "Administration portal")
        self.assertContains(dashboard, "Published events")
        self.assertContains(dashboard, "Create an event")
        self.assertContains(dashboard, "<strong>1</strong>", html=True)

        event_list = self.client.get(reverse("admin:events_event_changelist"))
        self.assertEqual(event_list.status_code, 200)
        self.assertContains(event_list, self.event.title)
