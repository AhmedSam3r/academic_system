from django.core import validators
from django.db import models


class Enrollment(models.Model):
    # TODO utilize Django’s ORM optimization techniques
    # TODO (e.g., aggregation, indexing, or materialized view
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    student = models.ForeignKey(
        "students.student",
        on_delete=models.CASCADE,
        related_name="enrollments",
        db_index=True,
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
        max_length=20,
        choices=Status.choices,
        db_default=Status.PENDING,
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    @classmethod
    def students_per_region(cls):
        return (
            Enrollment.objects.values("region")
            .annotate(total_students=models.Count("id"))
            .order_by("-total_students")
        )

    @classmethod
    def students_per_grade(cls):
        return (
            Enrollment.objects.values("grade")
            .annotate(total_students=models.Count("id"))
            .order_by("-total_students")
        )
