from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Department, Program, Student
from .student_identity import validate_student_identity_email


class StudentSignupForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    middle_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=150)
    student_id = forms.RegexField(
        regex=r"^\d{1,30}$",
        max_length=30,
        error_messages={"invalid": "Enter your numeric school-issued student ID."},
    )
    department = forms.ModelChoiceField(queryset=Department.objects.order_by("name"))
    program = forms.ModelChoiceField(
        queryset=Program.objects.select_related("department").order_by(
            "department__name", "name"
        )
    )
    year_level = forms.ChoiceField(choices=Student.YearLevel.choices)
    email = forms.EmailField(
        max_length=150,
        help_text=(
            "Use lastname.StudentIDNumber@"
            f"{settings.INSTITUTIONAL_EMAIL_DOMAIN}."
        ),
    )
    password = forms.CharField(
        min_length=8,
        strip=False,
        widget=forms.PasswordInput,
    )
    confirm_password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        for name in ("department", "program", "year_level"):
            self.fields[name].widget.attrs["class"] = "form-select"

    def clean_student_id(self):
        student_id = self.cleaned_data["student_id"].strip()
        if Student.objects.filter(student_id=student_id).exists():
            raise ValidationError("This student ID is already registered.")
        return student_id

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        last_name = self.cleaned_data.get("last_name")
        student_id = self.cleaned_data.get("student_id")
        if not last_name or not student_id:
            return email
        try:
            email, student_id = validate_student_identity_email(
                last_name,
                student_id,
                email,
            )
        except ValidationError as error:
            if hasattr(error, "message_dict") and "email" in error.message_dict:
                raise ValidationError(error.message_dict["email"]) from error
            raise
        if User.objects.filter(username=email).exists():
            raise ValidationError("An account with this email already exists.")
        if Student.objects.filter(student_id=student_id).exists():
            raise ValidationError("This student ID is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get("department")
        program = cleaned_data.get("program")
        if department and program and program.department_id != department.id:
            self.add_error("program", "Choose a program in the selected department.")

        password = cleaned_data.get("password")
        confirmation = cleaned_data.get("confirm_password")
        if password and confirmation and password != confirmation:
            self.add_error("confirm_password", "Passwords do not match.")
        if password and cleaned_data.get("email"):
            candidate = User(
                username=cleaned_data["email"],
                email=cleaned_data["email"],
                first_name=cleaned_data.get("first_name", ""),
                last_name=cleaned_data.get("last_name", ""),
            )
            try:
                validate_password(password, user=candidate)
            except ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    @transaction.atomic
    def create_student(self):
        data = self.cleaned_data
        user = User(
            username=data["email"],
            email=data["email"],
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
        )
        user.set_password(data["password"])
        user.full_clean()
        user.save()
        student = Student(
            user=user,
            middle_name=data["middle_name"].strip(),
            department=data["department"],
            program=data["program"],
            year_level=int(data["year_level"]),
            student_id=data["student_id"],
        )
        student.full_clean()
        student.save()
        return student


class StudentLoginForm(forms.Form):
    email = forms.EmailField(max_length=150)
    password = forms.CharField(strip=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()
