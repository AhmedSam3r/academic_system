import logging
import uuid
from typing import Any

from django.utils import timezone

from config import settings
from students.models import Student

from .models import Enrollment, EnrollmentBatch, Status

logger = logging.getLogger(__name__)

batch_size = settings.CELERY_ENROLLMENT_BATCH_SIZE


def validate_enrollment_batch(batch_id: uuid.UUID, task_id: uuid.UUID):
    try:
        # handle idempotency with batch id and status pending ignore
        batch = EnrollmentBatch.objects.get(id=batch_id)
        if batch and batch.status not in {Status.PENDING}:
            # TODO we can resend the task to retry queue
            logger.info(
                f"Skip batch {batch_id} in terminal state '{batch.status}'."
            )  # noqa: E501
            return

        EnrollmentBatch.objects.filter(id=batch_id).update(
            status=Status.INPROGRESS,
            task_id=task_id,
        )
        return batch

    except EnrollmentBatch.DoesNotExist:
        logger.error(f"Batch {batch_id} not found — discarding.")

    return None


def build_students_objects(enrollments: list[dict[str, Any]]):
    student_map: dict[str, Student] = {}
    student_rows = []
    for row in enrollments:
        email = row.get("student_email")
        name = row.get("student_name")
        # Reuse the same Student object if email appears multiple
        # times in the batch — last write wins for name/region/grade.
        student_map[email] = Student(
            email=email,
            name=name,
        )
        student_rows.append(row)

    return student_map, student_rows


def create_or_update_students(
    enrollments: list[dict[str, Any]],
):
    student_map, student_objects = build_students_objects(
        enrollments=enrollments,
    )
    student_objects = list(student_map.values())
    for chunk_start in range(0, len(student_objects), batch_size):
        chunk = student_objects[chunk_start:chunk_start + batch_size]
        Student.objects.bulk_create(
            objs=chunk,
            batch_size=batch_size,
            update_conflicts=True,
            update_fields=["name", "updated_at"],
            unique_fields=["email"],
        )

    # Fetch back persisted students to get their real PKs
    emails = list(student_map.keys())
    # query using one trip to DB
    persisted_map = {
        s.email: s for s in Student.objects.filter(
            email__in=emails).only("id", "email")
    }
    result = {
        "persisted_map": persisted_map,
        "student_objects": student_objects,
    }
    return result


def build_enrollments_objects(
    batch_id: uuid.UUID,
    enrollment_data: list[dict[str, Any]],
    persisted_map: dict[str, Student],
):
    success_objs: list[Enrollment] = []
    failed_objs: list[Enrollment] = []

    for item in enrollment_data:
        email = item["student_email"]
        student = persisted_map.get(email)  # contains id
        status = Status.SUCCESS if student else Status.FAILED
        error_message = (
            "" if student else f"Student with email {email} not found."
        )  # noqa: E501

        enrollment_obj = Enrollment(
            batch_id=batch_id,
            student_id=student.id if student else None,  # TODO fix that logic
            grade=item["grade"],
            region=item["region"],
            school=item["school"],
            status=status,
            error_message=error_message,
        )
        if student:
            success_objs.append(enrollment_obj)
        else:
            failed_objs.append(enrollment_obj)

    return success_objs, failed_objs


def create_enrollments(
    batch_id: uuid.UUID,
    enrollment_data: list[dict[str, Any]],
    persisted_map: dict[str, Student],
    total_count: int,
):
    success_objs, failed_objs = build_enrollments_objects(
        batch_id,
        enrollment_data,
        persisted_map,
    )
    db_failed_count = 0
    all_objs = success_objs + failed_objs

    for chunk_start in range(0, len(all_objs), batch_size):
        chunk = all_objs[chunk_start:chunk_start + batch_size]
        try:
            Enrollment.objects.bulk_create(
                objs=chunk,
                batch_size=batch_size,
                update_conflicts=True,
                update_fields=["status", "error_message"],
                unique_fields=["batch", "student_id"],
            )
        except Exception as db_exc:
            exc_msg = f"Chunk insert failed at {chunk_start} with batch_id: {batch_id}"  # noqa: E501
            logger.exception(exc_msg)
            db_failed_count += sum(
                1 for obj in chunk if obj.status == Status.PROCESSED
            )
            obj: Enrollment
            for obj in chunk:
                obj.status = Status.FAILED
                obj.error_message = f"DB error: {db_exc}"
                obj.save()

    total_failed = len(failed_objs) + db_failed_count
    total_success = total_count - total_failed

    if total_failed == 0:
        final_status = Status.PROCESSED
    elif total_success == 0:
        final_status = Status.FAILED
    else:
        final_status = Status.PARTIAL

    EnrollmentBatch.objects.filter(id=batch_id).update(
        status=final_status,
        total_count=total_count,
        processed_count=total_success,
        failed_count=total_failed,
        completed_at=timezone.now(),
    )
    logger.info(
        f"Batch {batch_id} - {final_status} | "
        f"total={total_count} success={total_success}"
        f" failed={total_failed}"
    )
