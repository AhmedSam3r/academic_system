from django.core import validators
from rest_framework import serializers

from .models import EnrollmentBatch


class EnrollmentStatsQuerySerializer(serializers.Serializer):
    group_by = serializers.ChoiceField(
        choices=["region", "grade"],
        help_text="Field used to group students",
    )


class EnrollmentItemSerializer(serializers.Serializer):
    student_name = serializers.CharField(min_length=3, max_length=255)
    student_email = serializers.EmailField(min_length=3, max_length=255)
    region = serializers.CharField(min_length=3, max_length=255)
    grade = serializers.CharField(min_length=3, max_length=255)
    school = serializers.CharField(min_length=3, max_length=255)


class EnrollmentCreateSerializer(serializers.Serializer):
    enrollments = EnrollmentItemSerializer(
        many=True,
        validators=[
            validators.MinLengthValidator(1),
            validators.MaxLengthValidator(1000),
        ],
    )


class EnrollmentBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnrollmentBatch
        fields = [
            "id",
            "status",
            "total_count",
            "processed_count",
            "failed_count",
            "created_at",
        ]
