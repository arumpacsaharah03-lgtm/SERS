import json
from datetime import datetime
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .forms import StudentLoginForm, StudentSignupForm
from .models import Department, Event, Program, Registration, Student
from .student_identity import validate_student_identity_email


def payload(request):
    if request.content_type == "application/json":
        try:
            return json.loads(request.body or "{}")
        except json.JSONDecodeError as exc:
            raise ValidationError("Request body must contain valid JSON.") from exc
    return request.POST.dict()


def errors_response(error, status=400):
    if isinstance(error, ValidationError):
        if hasattr(error, "message_dict"):
            errors = error.message_dict
        else:
            errors = {"non_field_errors": error.messages}
    else:
        errors = {"non_field_errors": [str(error)]}
    return JsonResponse({"ok": False, "errors": errors}, status=status)


def related_object(model, object_id, field):
    try:
        return model.objects.get(pk=object_id)
    except (model.DoesNotExist, ValueError, TypeError) as exc:
        raise ValidationError({field: "The selected record does not exist."}) from exc


def require_user(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"ok": False, "error": "Authentication required."}, status=401
            )
        return view(request, *args, **kwargs)

    return wrapped


def require_admin(view):
    @wraps(view)
    @require_user
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse(
                {"ok": False, "error": "Administrator access required."},
                status=403,
            )
        return view(request, *args, **kwargs)

    return wrapped


def student_data(student):
    return {
        "id": student.id,
        "studentId": student.student_id,
        "firstName": student.user.first_name,
        "middleName": student.middle_name,
        "lastName": student.user.last_name,
        "fullName": student.full_name,
        "email": student.user.email,
        "department": {
            "id": student.department_id,
            "name": student.department.name,
        },
        "program": {"id": student.program_id, "name": student.program.name},
        "yearLevel": student.get_year_level_display(),
    }


def event_data(event):
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "category": event.category,
        "eventDate": event.event_date.isoformat(),
        "startTime": event.start_time.strftime("%H:%M"),
        "endTime": event.end_time.strftime("%H:%M"),
        "venue": event.venue,
        "registrationDeadline": event.registration_deadline.isoformat(),
        "maximumParticipants": event.maximum_participants,
        "registeredParticipants": event.registrations.count(),
        "image": event.image.url if event.image else None,
        "status": event.status,
    }


def registration_data(registration):
    return {
        "id": registration.id,
        "student": student_data(registration.student),
        "event": event_data(registration.event),
        "status": registration.status,
        "rejectionReason": registration.rejection_reason,
        "registrationDate": registration.created_at.isoformat(),
        "reviewedAt": (
            registration.reviewed_at.isoformat()
            if registration.reviewed_at
            else None
        ),
    }


@require_http_methods(["GET"])
def health(request):
    return JsonResponse(
        {
            "ok": True,
            "service": "School Event Registration System",
            "database": "configured",
        }
    )


@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf_token(request):
    from django.middleware.csrf import get_token

    return JsonResponse({"ok": True, "csrfToken": get_token(request)})


@require_http_methods(["POST"])
def signup(request):
    try:
        data = payload(request)
        allowed = {
            "lastName",
            "firstName",
            "middleName",
            "studentId",
            "departmentId",
            "programId",
            "yearLevel",
            "email",
            "password",
            "confirmPassword",
        }
        data = {key: value for key, value in data.items() if key in allowed}
        required = [
            "lastName",
            "firstName",
            "studentId",
            "departmentId",
            "programId",
            "yearLevel",
            "email",
            "password",
            "confirmPassword",
        ]
        missing = [field for field in required if not str(data.get(field, "")).strip()]
        if missing:
            raise ValidationError({field: "This field is required." for field in missing})

        email = str(data["email"]).strip().lower()
        email, student_id = validate_student_identity_email(
            data["lastName"],
            data["studentId"],
            email,
            student_id_field="studentId",
        )
        if Student.objects.filter(student_id=student_id).exists():
            raise ValidationError(
                {"studentId": "This student ID is already registered."}
            )
        if data["password"] != data["confirmPassword"]:
            raise ValidationError({"confirmPassword": "Passwords do not match."})
        if len(data["password"]) < 8:
            raise ValidationError(
                {"password": "Password must contain at least 8 characters."}
            )
        department = related_object(
            Department, data["departmentId"], "departmentId"
        )
        program = related_object(Program, data["programId"], "programId")
        if program.department_id != department.id:
            raise ValidationError(
                {"programId": "The program does not belong to this department."}
            )

        with transaction.atomic():
            user = User(
                username=email,
                email=email,
                first_name=str(data["firstName"]).strip(),
                last_name=str(data["lastName"]).strip(),
            )
            user.set_password(data["password"])
            user.full_clean()
            user.save()
            student = Student(
                user=user,
                middle_name=str(data.get("middleName", "")).strip(),
                department=department,
                program=program,
                year_level=int(data["yearLevel"]),
                student_id=student_id,
            )
            student.full_clean()
            student.save()
        return JsonResponse(
            {"ok": True, "student": student_data(student)}, status=201
        )
    except (ValidationError, ValueError, TypeError, IntegrityError) as exc:
        if isinstance(exc, IntegrityError):
            exc = ValidationError(
                {"email": "An account with this email or student ID already exists."}
            )
        return errors_response(exc)


@require_http_methods(["POST"])
def sign_in(request):
    try:
        data = payload(request)
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        role = str(data.get("role", "student")).lower()
        user = authenticate(request, username=email, password=password)
        if user is None or not user.is_active:
            return JsonResponse(
                {"ok": False, "error": "Invalid email or password."}, status=401
            )
        if role == "admin" and not user.is_staff:
            return JsonResponse(
                {"ok": False, "error": "Administrator access required."}, status=403
            )
        if role == "student" and not hasattr(user, "student"):
            return JsonResponse(
                {"ok": False, "error": "Student account required."}, status=403
            )
        login(request, user)
        return JsonResponse(
            {
                "ok": True,
                "role": "admin" if user.is_staff else "student",
                "student": student_data(user.student)
                if hasattr(user, "student")
                else None,
            }
        )
    except ValidationError as exc:
        return errors_response(exc)


@require_http_methods(["POST"])
@require_user
def sign_out(request):
    logout(request)
    return JsonResponse({"ok": True})


@require_http_methods(["GET", "PATCH"])
@require_user
def profile(request):
    if request.user.is_staff or not hasattr(request.user, "student"):
        return JsonResponse({"ok": False, "error": "Student account required."}, status=403)
    student = request.user.student
    if request.method == "GET":
        return JsonResponse({"ok": True, "student": student_data(student)})
    try:
        data = payload(request)
        if "email" in data:
            raise ValidationError({"email": "Institutional email cannot be changed."})
        allowed = {"firstName", "lastName", "middleName", "departmentId", "programId", "yearLevel"}
        data = {key: value for key, value in data.items() if key in allowed}
        student.user.first_name = data.get("firstName", student.user.first_name)
        student.user.last_name = data.get("lastName", student.user.last_name)
        student.middle_name = data.get("middleName", student.middle_name)
        if "departmentId" in data:
            student.department = related_object(
                Department, data["departmentId"], "departmentId"
            )
        if "programId" in data:
            student.program = related_object(
                Program, data["programId"], "programId"
            )
        if "yearLevel" in data:
            student.year_level = int(data["yearLevel"])
        student.full_clean()
        with transaction.atomic():
            student.user.save(update_fields=["first_name", "last_name"])
            student.save()
        return JsonResponse({"ok": True, "student": student_data(student)})
    except (ValidationError, ValueError, TypeError) as exc:
        return errors_response(exc)


def apply_event_fields(event, data):
    mapping = {
        "title": "title",
        "description": "description",
        "category": "category",
        "eventDate": "event_date",
        "startTime": "start_time",
        "endTime": "end_time",
        "venue": "venue",
        "registrationDeadline": "registration_deadline",
        "maximumParticipants": "maximum_participants",
        "status": "status",
    }
    for source, target in mapping.items():
        if source in data:
            setattr(event, target, data[source])
    event.full_clean()
    return event


@require_http_methods(["GET", "POST"])
@require_user
def event_list(request):
    if request.method == "POST":
        if not request.user.is_staff:
            return JsonResponse(
                {"ok": False, "error": "Administrator access required."}, status=403
            )
        try:
            event = apply_event_fields(Event(created_by=request.user), payload(request))
            if request.FILES.get("image"):
                event.image = request.FILES["image"]
            event.save()
            return JsonResponse({"ok": True, "event": event_data(event)}, status=201)
        except (ValidationError, ValueError, TypeError) as exc:
            return errors_response(exc)

    queryset = Event.objects.all()
    if not request.user.is_staff:
        queryset = queryset.filter(status=Event.Status.PUBLISHED)
    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(venue__icontains=search)
        )
    if category:
        queryset = queryset.filter(category=category)
    if status and request.user.is_staff:
        queryset = queryset.filter(status=status)
    return JsonResponse({"ok": True, "events": [event_data(item) for item in queryset]})


@require_http_methods(["GET", "PATCH", "DELETE"])
@require_user
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == "GET":
        if not request.user.is_staff and event.status != Event.Status.PUBLISHED:
            return JsonResponse({"ok": False, "error": "Event not found."}, status=404)
        return JsonResponse({"ok": True, "event": event_data(event)})
    if not request.user.is_staff:
        return JsonResponse(
            {"ok": False, "error": "Administrator access required."}, status=403
        )
    if request.method == "DELETE":
        event.delete()
        return JsonResponse({"ok": True})
    try:
        apply_event_fields(event, payload(request))
        if request.FILES.get("image"):
            event.image = request.FILES["image"]
        event.save()
        return JsonResponse({"ok": True, "event": event_data(event)})
    except (ValidationError, ValueError, TypeError) as exc:
        return errors_response(exc)


@require_http_methods(["GET", "POST"])
@require_user
def registration_list(request):
    if request.method == "GET":
        queryset = Registration.objects.select_related(
            "student__user", "student__department", "student__program", "event"
        )
        if not request.user.is_staff:
            if not hasattr(request.user, "student"):
                return JsonResponse(
                    {"ok": False, "error": "Student account required."}, status=403
                )
            queryset = queryset.filter(student=request.user.student)
        event_id = request.GET.get("event")
        status = request.GET.get("status")
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        if status:
            queryset = queryset.filter(status=status)
        return JsonResponse(
            {
                "ok": True,
                "registrations": [registration_data(item) for item in queryset],
            }
        )

    if request.user.is_staff or not hasattr(request.user, "student"):
        return JsonResponse({"ok": False, "error": "Student account required."}, status=403)
    try:
        data = payload(request)
        event = related_object(Event, data.get("eventId"), "eventId")
        if event.status != Event.Status.PUBLISHED:
            raise ValidationError({"eventId": "This event is not open for registration."})
        if event.registration_deadline < timezone.now():
            raise ValidationError({"eventId": "The registration deadline has passed."})
        if event.registrations.count() >= event.maximum_participants:
            raise ValidationError({"eventId": "This event has reached its capacity."})
        with transaction.atomic():
            registration = Registration.objects.create(
                student=request.user.student, event=event
            )
        return JsonResponse(
            {"ok": True, "registration": registration_data(registration)}, status=201
        )
    except IntegrityError:
        return errors_response(
            ValidationError({"eventId": "You are already registered for this event."})
        )
    except (ValidationError, ValueError, TypeError) as exc:
        return errors_response(exc)


@require_http_methods(["PATCH"])
@require_admin
def registration_status(request, registration_id):
    registration = get_object_or_404(Registration, pk=registration_id)
    try:
        data = payload(request)
        status = data.get("status")
        if status not in Registration.Status.values:
            raise ValidationError({"status": "Choose Approved, Pending, or Rejected."})
        if status == Registration.Status.APPROVED:
            approved = Registration.objects.filter(
                event=registration.event, status=Registration.Status.APPROVED
            ).exclude(pk=registration.pk)
            if approved.count() >= registration.event.maximum_participants:
                raise ValidationError({"status": "The event has reached its capacity."})
        registration.status = status
        registration.rejection_reason = (
            str(data.get("rejectionReason", "")).strip()
            if status == Registration.Status.REJECTED
            else ""
        )
        registration.reviewed_by = request.user
        registration.reviewed_at = timezone.now()
        registration.save()
        return JsonResponse(
            {"ok": True, "registration": registration_data(registration)}
        )
    except (ValidationError, ValueError, TypeError) as exc:
        return errors_response(exc)


@require_http_methods(["GET"])
@require_admin
def reports(request):
    event_rows = (
        Event.objects.annotate(
            total=Count("registrations"),
            approved=Count(
                "registrations",
                filter=Q(registrations__status=Registration.Status.APPROVED),
            ),
            pending=Count(
                "registrations",
                filter=Q(registrations__status=Registration.Status.PENDING),
            ),
            rejected=Count(
                "registrations",
                filter=Q(registrations__status=Registration.Status.REJECTED),
            ),
        )
        .values("id", "title", "total", "approved", "pending", "rejected")
        .order_by("event_date")
    )
    return JsonResponse(
        {
            "ok": True,
            "summary": {
                "students": Student.objects.filter(is_active=True).count(),
                "events": Event.objects.count(),
                "registrations": Registration.objects.count(),
                "pending": Registration.objects.filter(
                    status=Registration.Status.PENDING
                ).count(),
            },
            "events": list(event_rows),
        }
    )


def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("admin:index")
        if hasattr(request.user, "student"):
            return redirect("student-dashboard")
    return redirect("student-login")


@require_http_methods(["GET", "POST"])
def student_signup(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return home(request)
    form = StudentSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            form.create_student()
        except IntegrityError:
            form.add_error("email", "An account with this email already exists.")
        else:
            messages.success(request, "Your account was created. You can now sign in.")
            return redirect("student-login")
    programs = Program.objects.select_related("department").order_by(
        "department__name", "name"
    )
    return render(
        request,
        "events/student_signup.html",
        {
            "form": form,
            "programs": list(
                programs.values("id", "department_id", "name", "code")
            ),
        },
    )


@require_http_methods(["GET", "POST"])
def student_login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return home(request)
    form = StudentLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        if user is None or not user.is_active:
            form.add_error(None, "Invalid email or password.")
        elif user.is_staff:
            return redirect("admin:index")
        elif not hasattr(user, "student"):
            form.add_error(None, "This account is not registered as a student.")
        else:
            login(request, user)
            return redirect("student-dashboard")
    return render(request, "events/student_login.html", {"form": form})


def student_required(view):
    @login_required(login_url="student-login")
    def wrapped(request: HttpRequest, *args, **kwargs):
        if request.user.is_staff:
            return redirect("admin:index")
        if not hasattr(request.user, "student"):
            logout(request)
            messages.error(request, "Please sign in with a student account.")
            return redirect("student-login")
        return view(request, *args, **kwargs)

    wrapped.__name__ = view.__name__
    wrapped.__doc__ = view.__doc__
    return wrapped


@require_http_methods(["POST"])
@login_required(login_url="student-login")
def student_logout(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("student-login")


@student_required
def student_dashboard(request: HttpRequest) -> HttpResponse:
    student = request.user.student
    registrations = (
        Registration.objects.filter(student=student)
        .select_related("event")
        .order_by("-created_at")
    )
    return render(
        request,
        "events/student_dashboard.html",
        {
            "student": student,
            "available_count": Event.objects.filter(
                status=Event.Status.PUBLISHED,
                event_date__gte=timezone.localdate(),
            ).count(),
            "registrations": registrations[:5],
            "registration_count": registrations.count(),
            "approved_count": registrations.filter(
                status=Registration.Status.APPROVED
            ).count(),
            "pending_count": registrations.filter(
                status=Registration.Status.PENDING
            ).count(),
            "upcoming_events": Event.objects.filter(
                status=Event.Status.PUBLISHED,
                event_date__gte=timezone.localdate(),
            ).order_by("event_date", "start_time")[:3],
        },
    )


@student_required
def student_events(request: HttpRequest) -> HttpResponse:
    events = Event.objects.filter(
        status=Event.Status.PUBLISHED,
        event_date__gte=timezone.localdate(),
    ).annotate(registration_count=Count("registrations")).order_by(
        "event_date", "start_time"
    )
    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()
    if search:
        events = events.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(venue__icontains=search)
        )
    if category in Event.Category.values:
        events = events.filter(category=category)
    registered_event_ids = set(
        Registration.objects.filter(student=request.user.student).values_list(
            "event_id", flat=True
        )
    )
    return render(
        request,
        "events/student_events.html",
        {
            "events": events,
            "categories": Event.Category.choices,
            "selected_category": category,
            "search": search,
            "registered_event_ids": registered_event_ids,
        },
    )


@student_required
@require_http_methods(["POST"])
def student_register(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(
        Event, pk=event_id, status=Event.Status.PUBLISHED
    )
    try:
        with transaction.atomic():
            locked_event = Event.objects.select_for_update().get(pk=event.pk)
            if locked_event.registration_deadline < timezone.now():
                messages.error(request, "The registration deadline has passed.")
            elif locked_event.event_date < timezone.localdate():
                messages.error(request, "This event has already taken place.")
            elif locked_event.registrations.count() >= locked_event.maximum_participants:
                messages.error(request, "This event has reached its participant limit.")
            else:
                Registration.objects.create(
                    student=request.user.student,
                    event=locked_event,
                )
                messages.success(request, "You are registered. Your request is pending approval.")
    except IntegrityError:
        messages.info(request, "You are already registered for this event.")
    return redirect("student-events")


@student_required
def student_registrations(request: HttpRequest) -> HttpResponse:
    registrations = (
        Registration.objects.filter(student=request.user.student)
        .select_related("event")
        .order_by("-created_at")
    )
    return render(
        request,
        "events/student_registrations.html",
        {"registrations": registrations},
    )


@student_required
def student_profile(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "events/student_profile.html",
        {"student": request.user.student},
    )
