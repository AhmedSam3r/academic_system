from django.core import validators
from django.db import models
from uuid_utils import uuid7


class Status(models.TextChoices):
    PENDING = "pending", "PENDING"
    INPROGRESS = "progress", "PROGRESS"
    PROCESSED = "processed", "PROCESSED"
    SUCCESS = "success", "SUCCESS"
    FAILED = "failed", "FAILED"
    PARTIAL = "partial", "PARTIAL"


class EnrollmentBatch(models.Model):
    """
    Created synchronously on the hot path — one row per API call.
    The Celery worker updates status, processed_count, and failed_count
    as it works through the payload.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
    )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        db_default=Status.PENDING,
        db_index=True,
    )

    total_count = models.PositiveIntegerField(default=0)
    processed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    task_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "EnrollmentBatch"
        verbose_name_plural = "EnrollmentBatches"
        indexes = [
            # Composite index: monitor dashboard filters by status + recency.
            models.Index(
                fields=["status", "-created_at"],
                name="batch_status_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Batch {self.id} with status: [{self.status}]"


class Enrollment(models.Model):
    # TODO utilize Django’s ORM optimization techniques
    # TODO (e.g., aggregation, indexing, or materialized view
    student = models.ForeignKey(
        "students.student",
        on_delete=models.CASCADE,
        related_name="enrollments",
        db_index=True,
    )
    batch = models.ForeignKey(
        "enrollments.EnrollmentBatch",
        on_delete=models.CASCADE,
        related_name="batch",
        db_index=True,
        null=True,
    )

    # TODO check whether grade needs normalization
    grade = models.CharField(
        validators=[
            validators.MinLengthValidator(3),
            validators.MaxLengthValidator(255),
        ],
    )
    region = models.CharField(
        validators=[
            validators.MinLengthValidator(3),
            validators.MaxLengthValidator(255),
        ],
    )
    school = models.CharField(
        validators=[
            validators.MinLengthValidator(3),
            validators.MaxLengthValidator(255),
        ],
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        db_default=Status.PENDING,
        db_index=True,
    )

    error_message = models.TextField(
        null=True,
        blank=True,
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        constraints = [
            # idempotency guard for creating student in the same batch > once
            models.UniqueConstraint(
                fields=["batch", "student_id"],
                name="unique_enrollment_per_batch",
            )
        ]

    @classmethod
    def students_per_region(cls):
        return (
            # TODO group by region
            Enrollment.objects.values("region")
            .annotate(total_students=models.Count("id"))
            .order_by("-total_students")
        )

    @classmethod
    def students_per_grade(cls):
        return (
            # TODO group by grade
            Enrollment.objects.values("grade")
            .annotate(total_students=models.Count("id"))
            .order_by("-total_students")
        )
