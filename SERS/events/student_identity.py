import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


def validate_student_identity_email(
    last_name, student_id, email, student_id_field="student_id"
):
    last_name = str(last_name).strip()
    student_id = str(student_id).strip()
    email = str(email).strip().lower()

    if not re.fullmatch(r"\d{1,30}", student_id):
        raise ValidationError(
            {
                student_id_field: (
                    "Enter your numeric school-issued student ID."
                )
            }
        )

    try:
        validate_email(email)
    except ValidationError as error:
        raise ValidationError({"email": error.messages}) from error

    expected_email = (
        f"{last_name.lower()}.{student_id}@"
        f"{settings.INSTITUTIONAL_EMAIL_DOMAIN}"
    )
    if email != expected_email:
        raise ValidationError(
            {
                "email": (
                    "Use your lowercase last name followed by a period, your "
                    f"student ID, and @{settings.INSTITUTIONAL_EMAIL_DOMAIN} "
                    "(for example: doe.1003899@msusnd.edu.ph)."
                )
            }
        )

    return email, student_id
